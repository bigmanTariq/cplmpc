from flask import Flask, request, redirect, url_for, send_file, render_template
from PyPDF2 import PdfMerger, PdfWriter
from io import BytesIO

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_files():
    files = request.files.getlist('pdf_files')
    if not files or len(files) == 0:
        return 'No files uploaded!', 400

    merger = PdfMerger()
    exhibit_counter = 3

    for file in files:
        merger.append(file)

        # Add a blank page with "Exhibit" and a number placeholder
        blank_pdf = BytesIO()
        writer = PdfWriter()

        # Create a blank page
        writer.add_blank_page(width=210, height=297)
        writer.add_metadata({
            '/Title': f'Exhibit {exhibit_counter}'
        })

        writer.write(blank_pdf)
        blank_pdf.seek(0)

        merger.append(blank_pdf)

        exhibit_counter += 1

    output = BytesIO()
    merger.write(output)
    output.seek(0)

    return send_file(output, as_attachment=True, download_name='merged_with_exhibits.pdf', mimetype='application/pdf')

if __name__ == '__main__':
    app.run(debug=True)
