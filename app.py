import os
from datetime import datetime
import io
import zipfile
from flask import Flask, request, jsonify, send_file, redirect, url_for
from rembg import remove

app = Flask(__name__)

class BackgroundRemover:
    def __init__(self, output_folder):
        self.output_folder = output_folder

    def remove_background(self, input_data, output_path):
        with open(output_path, "wb") as outp:
            background_output = remove(input_data.read())
            outp.write(background_output)

@app.route('/')
def index():
    return '''
    <form method="POST" action="/process" enctype="multipart/form-data">
        <input type="file" name="files[]" accept=".png, .jpg, .jpeg" multiple>
        <input type="submit" value="Procesar">
    </form>
    '''

@app.route('/process', methods=['POST'])
def process_images():
    output_folder = 'output'
    remover = BackgroundRemover(output_folder)

    if 'files[]' not in request.files:
        return jsonify({'error': 'No se han proporcionado archivos'}), 400

    files = request.files.getlist('files[]')

    if not files:
        return jsonify({'error': 'No se han proporcionado archivos'}), 400

    today = datetime.now().strftime("%Y-%m-%d %H-%M-%S")
    processed_folder = os.path.join(output_folder, today)
    os.makedirs(processed_folder, exist_ok=True)

    zip_filename = f'{today}_processed_images.zip'
    zip_buffer = io.BytesIO()

    for file in files:
        if file.filename == '':
            continue

        output_path = os.path.join(processed_folder, file.filename)
        remover.remove_background(file, output_path)

        # Comprime las imágenes procesadas en un archivo ZIP
        with zipfile.ZipFile(zip_buffer, 'a', zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(output_path, os.path.basename(output_path))

    zip_buffer.seek(0)
    return send_file(zip_buffer, as_attachment=True, download_name=zip_filename)

if __name__ == '__main__':
    app.run(debug=True)
