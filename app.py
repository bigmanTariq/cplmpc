from flask import Flask, request, send_file, render_template
from PyPDF2 import PdfMerger, PdfReader
from io import BytesIO
from reportlab.pdfgen import canvas
from PIL import Image
import fitz  # PyMuPDF

app = Flask(__name__)

def create_exhibit_page(exhibit_number, page_width, page_height):
    packet = BytesIO()
    can = canvas.Canvas(packet, pagesize=(float(page_width), float(page_height)))
    can.setFont("Helvetica", 30)
    
    text = f"Exhibit {exhibit_number}"
    text_width = can.stringWidth(text, "Helvetica", 30)
    
    x_position = (float(page_width) - text_width) / 2
    y_position = (float(page_height) / 2)
    
    can.drawString(x_position, y_position, text)
    can.save()
    packet.seek(0)
    return packet

def optimize_images(pdf_stream):
    doc = fitz.open(stream=pdf_stream, filetype="pdf")
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        images = page.get_images(full=True)
        for img_index, img in enumerate(images):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            image = Image.open(BytesIO(image_bytes))
            # Compress the image
            image = image.convert("RGB")
            image_bytes_io = BytesIO()
            image.save(image_bytes_io, format='JPEG', quality=50)  # Adjust quality as needed
            new_image_bytes = image_bytes_io.getvalue()

            # Extract image rectangle coordinates
            bbox = img[2:6]
            print(f"Page {page_num}, Image {img_index}, bbox: {bbox}")
            try:
                rect = fitz.Rect(*bbox)
                page.insert_image(rect, stream=new_image_bytes, keep_proportion=True)
            except Exception as e:
                print(f"Error processing image {img_index} on page {page_num}: {e}")
    optimized_pdf = BytesIO()
    doc.save(optimized_pdf)
    doc.close()
    optimized_pdf.seek(0)
    return optimized_pdf

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_files():
    files = request.files.getlist('pdf_files')
    if not files or len(files) == 0:
        return 'No files uploaded!', 400

    merger = PdfMerger()
    exhibit_counter = 4

    for file in files:
        reader = PdfReader(file)
        page = reader.pages[0]  # Get the first page to determine size
        width = page.mediabox.width
        height = page.mediabox.height

        # Create a blank page with "Exhibit" and a number
        exhibit_page = create_exhibit_page(exhibit_counter, width, height)
        exhibit_reader = PdfReader(exhibit_page)
        merger.append(exhibit_reader)

        # Append the actual PDF file
        merger.append(file)

        exhibit_counter += 1

    output = BytesIO()
    merger.write(output)
    output.seek(0)
    merger.close()

    # Optimize images in the PDF
    optimized_pdf = optimize_images(output)

    # Optimize the PDF with PyMuPDF
    final_output = BytesIO()
    pdf_document = fitz.open(stream=optimized_pdf, filetype="pdf")
    pdf_document.save(final_output, garbage=4, deflate=True)
    final_output.seek(0)

    return send_file(final_output, mimetype='application/pdf')

if __name__ == '__main__':
    app.run(debug=True, port=5200, host='127.0.0.1')

