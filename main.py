import os
from datetime import datetime
import io
import zipfile
from flask import Flask, request, jsonify, send_file, redirect, url_for
from rembg import remove

app = Flask(__name__)

class BackgroundRemover:
    def __init__(self, input_folder, output_folder):
        self.input_folder = input_folder
        self.output_folder = output_folder

    def remove_background(self, input_path, output_path):
        with open(input_path, "rb") as inp, open(output_path, "wb") as outp:
            background_output = remove(inp.read())
            outp.write(background_output)

    def move_original(self, input_path, dest_path):
        originals_folder = os.path.join(dest_path, 'originals')
        os.makedirs(originals_folder, exist_ok=True)

        filename = os.path.basename(input_path)
        new_path = os.path.join(originals_folder, filename)
        os.rename(input_path, new_path)

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
    input_folder = 'input'
    output_folder = 'output'
    remover = BackgroundRemover(input_folder, output_folder)

    if 'file' not in request.files:
        return jsonify({'error': 'No se ha proporcionado un archivo'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'Nombre de archivo vacío'}), 400

    if file:
        today = datetime.now().strftime("%Y-%m-%d %H-%M-%S")
        processed_folder = os.path.join(output_folder, today)
        os.makedirs(processed_folder, exist_ok=True)

        input_path = os.path.join(input_folder, file.filename)
        output_path = os.path.join(processed_folder, file.filename)

        # Guarda el archivo en la carpeta de entrada
        file.save(input_path)

        # Elimina el fondo y mueve el archivo original
        remover.remove_background(input_path, output_path)
        remover.move_original(input_path, processed_folder)

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
