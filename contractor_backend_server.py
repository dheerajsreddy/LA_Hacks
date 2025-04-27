from flask import Flask, request, jsonify
from contractor_backend import (
    get_search_term_from_gemini,
    find_contractors_google_places
)

app = Flask(__name__)

@app.route('/search', methods=['POST'])
def search():
    data = request.json
    user_query = data['user_query']
    location = data.get('location', 'Los Angeles, CA')
    search_term = get_search_term_from_gemini(user_query)
    # For now, use default LA coordinates
    contractors = find_contractors_google_places(
        search_term=search_term,
        latitude=34.0522,
        longitude=-118.2437,
        radius=15 * 1609
    )
    return jsonify({'contractors': contractors})

if __name__ == '__main__':
    app.run(port=5002) 