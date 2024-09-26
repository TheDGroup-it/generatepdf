from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
import os
import tempfile
import zipfile
from werkzeug.utils import secure_filename
from test_addqrcodes_final import add_qr_codes_to_a3

app = Flask(__name__, template_folder='templates')
app.secret_key = 'your_secret_key'  # Needed for flash messages

UPLOAD_FOLDER = 'uploads/'
OUTPUT_FOLDER = 'outputs/'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template('index_original.html')

@app.route('/generate_pdf', methods=['POST'])
def generate_pdf():
    uploaded_files = request.files.getlist('inputfolder')  # Get the list of uploaded files
    outputfolder = request.form['outputfolder']
    titlepage = request.form['titlepage']
    outputfile = request.form['outputfile']

    # Ensure output file ends with .pdf
    if not outputfile.endswith('.pdf'):
        outputfile += '.pdf'

    # Create a unique temporary directory within the project directory
    temp_dir = os.path.join(UPLOAD_FOLDER, secure_filename(outputfile))
    os.makedirs(temp_dir, exist_ok=True)

    input_folder = temp_dir

    for file in uploaded_files:
        if file and file.filename.endswith('.zip'):
            zip_path = os.path.join(input_folder, secure_filename(file.filename))
            file.save(zip_path)

            # Unzip the file, r as read
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(input_folder)
        else:
            filename = secure_filename(file.filename)
            file_path = os.path.join(input_folder, filename)
            file.save(file_path)
    try:
        # Debugging: Print paths
        print(f"Output folder: {outputfolder}")
        print(f"Output file: {outputfile}")

        # Call your add_qr_codes_to_a3 function
        add_qr_codes_to_a3(input_folder, outputfolder, titlepage, outputfile)
        #message = f"PDF {outputfile} created successfully!"
        #downloadpdf = f'<a href="{url_for('download_file', filename=filename)}" target="_blank">Click here to view and download PDF file.</a>'
    except Exception as e:
        message = f"Error: {str(e)}"
    #return render_template('index_original.html', message=message, downloadpdf=downloadpdf)

    # Redirect to the completion route with a message and filename
    #return redirect(url_for('generate_pdf_complete', message=message, filename=outputfile))
    return redirect(url_for('generate_pdf_complete', filename=outputfile))

@app.route('/generate_pdf_complete')
def generate_pdf_complete():
    messagetext = request.args.get('message', 'PDF generated successfully!')
    filename_text = request.args.get('filename')
    print(f"Filename : {filename_text}") # Successful, it show the filename in console
    if not filename_text:
        return "Filename not provided", 400  # Handle missing filename
    # Error does not show text for "downloadpdf"
    downloadpdf = f'<a href="{url_for("download_file", filename=filename_text)}" target="_blank">Click here to view and download PDF file.</a>'
    return render_template('index_original.html', message=messagetext, downloadpdf=downloadpdf) 

@app.route('/outputs/<filename>')
def download_file(filename):
    return send_from_directory(OUTPUT_FOLDER, filename)

if __name__ == '__main__':
    app.run(debug=True)
