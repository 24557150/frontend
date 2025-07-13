from flask import Flask, request, send_file
from flask_cors import CORS
from utils import remove_background
import os

app = Flask(__name__)
CORS(app)  # 解決 CORS 跨網域問題

@app.route('/remove_bg', methods=['POST'])
def remove_bg():
    image = request.files['image']
    image_path = f"temp_input.png"
    output_path = f"temp_output.png"

    image.save(image_path)
    remove_background(image_path, output_path)
    return send_file(output_path, mimetype='image/png')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

