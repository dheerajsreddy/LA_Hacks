from flask import Flask, request, jsonify
import os
from homedepot_backend import (
    get_search_query_from_gemini,
    search_home_depot_serpapi,
    download_product_images
)

app = Flask(__name__)

@app.route('/search', methods=['POST'])
def search():
    data = request.json
    user_query = data['user_query']
    serpapi_key = data['serpapi_key']
    search_query = get_search_query_from_gemini(user_query)
    products = search_home_depot_serpapi(serpapi_key, search_query)
    return jsonify({'products': products})

@app.route('/download_images', methods=['POST'])
def download_images():
    data = request.json
    products = data['products']
    images_dir = data['images_dir']
    downloaded_images = download_product_images(products, images_dir)
    return jsonify({'downloaded_images': [str(p) for p in downloaded_images]})

if __name__ == '__main__':
    app.run(port=5001) 