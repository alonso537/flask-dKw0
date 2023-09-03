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
        <input type="file" name="file" accept=".png, .jpg, .jpeg">
        <input type="submit" value="Procesar">
    </form>
    '''

@app.route('/process', methods=['POST'])
def process_images():
    output_folder = 'output'
    remover = BackgroundRemover(output_folder)

    if 'file' not in request.files:
        return jsonify({'error': 'No se ha proporcionado un archivo'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'Nombre de archivo vacío'}), 400

    if file:
        today = datetime.now().strftime("%Y-%m-%d %H-%M-%S")
        processed_folder = os.path.join(output_folder, today)
        os.makedirs(processed_folder, exist_ok=True)

        output_path = os.path.join(processed_folder, file.filename)

        # Elimina el fondo y guarda el archivo directamente
        remover.remove_background(file, output_path)

        # Comprime las imágenes procesadas en un archivo ZIP
        zip_filename = f'{today}_processed_images.zip'
        zip_buffer = io.BytesIO()  # Crear el objeto BytesIO aquí

        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
            processed_folder = os.path.join(output_folder, today)
            for root, _, files in os.walk(processed_folder):
                for file in files:
                    file_path = os.path.join(root, file)
                    zipf.write(file_path, os.path.relpath(file_path, processed_folder))

        zip_buffer.seek(0)
        return send_file(zip_buffer, as_attachment=True, download_name=zip_filename)

if __name__ == '__main__':
    app.run(debug=True)
