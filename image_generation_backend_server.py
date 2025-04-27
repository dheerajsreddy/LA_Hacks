from flask import Flask, request, jsonify
from image_generation_backend import generate_room_image, generate_image_prompt
from pathlib import Path

app = Flask(__name__)

@app.route('/generate', methods=['POST'])
def generate():
    data = request.json
    room_image_path = Path(data['room_image_path'])
    product_image_path = Path(data['product_image_path'])
    user_query = data['user_query']
    output_path = Path(data['output_path'])

    image_prompt = generate_image_prompt(user_query)
    success = generate_room_image(room_image_path, product_image_path, user_query, output_path)
    return jsonify({'success': success, 'output_path': str(output_path), 'image_prompt': image_prompt})

if __name__ == '__main__':
    app.run(port=5003) 