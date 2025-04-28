from flask import Blueprint, request, jsonify
from movie_api import search_movies, get_movie_details
from movie_model import add_favorite, get_favorites

movies_bp = Blueprint('movies', __name__)

@movies_bp.route('/search', methods=['GET'])
def search():
    query = request.args.get('query')
    if not query:
        return jsonify({"error": "Missing 'query' parameter"}), 400
    results = search_movies(query)
    return jsonify(results)

@movies_bp.route('/favorites/<user_id>', methods=['GET', 'POST'])
def favorites(user_id):
    if request.method == 'POST':
        movie = request.json
        add_favorite(user_id, movie)
        return jsonify({"message": "Added to favorites"})
    else:
        return jsonify(get_favorites(user_id))
