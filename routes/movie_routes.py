from flask import Blueprint, jsonify, request, make_response
from flask_login import login_required, current_user
from catalog.utils.logger import configure_logger

movie_bp = Blueprint('movie', __name__)

user_favorites = {}

@movie_bp.route('/add-favorite', methods=['POST'])
@login_required
def add_favorite():
    """Add a favorite movie for the current user."""

    data = request.get_json()
    movie_id = data.get('movie_id')
    movie_title = data.get('movie_title')

    if not movie_id or not movie_title:
        return make_response(jsonify({
            "status": "error",
            "message": "movie_id and movie_title are required"
        }), 400)

    username = current_user.username

    # Initialize list if user doesn't exist yet
    if username not in user_favorites:
        user_favorites[username] = []

    # Add movie to the user's favorites
    user_favorites[username].append({
        "movie_id": movie_id,
        "movie_title": movie_title
    })

    return make_response(jsonify({
        "status": "success",
        "message": f"Movie '{movie_title}' added to favorites"
    }), 201)

@movie_bp.route('/get-favorites', methods=['GET'])
@login_required
def get_favorites():
    """Retrieve all favorite movies for the current user."""
    username = current_user.username
    favorites = user_favorites.get(username, [])

    return make_response(jsonify({
        "status": "success",
        "favorites": favorites
    }), 200)

@movie_bp.route('/delete-favorite', methods=['DELETE'])
@login_required
def delete_favorite():
    """Delete a favorite movie by movie_id for the current user."""

    data = request.get_json()
    movie_id = data.get('movie_id')

    if not movie_id:
        return make_response(jsonify({
            "status": "error",
            "message": "movie_id is required"
        }), 400)

    username = current_user.username
    favorites = user_favorites.get(username, [])

    # Remove the movie if it exists
    updated_favorites = [movie for movie in favorites if movie["movie_id"] != movie_id]

    if len(updated_favorites) == len(favorites):
        return make_response(jsonify({
            "status": "error",
            "message": f"Movie with ID {movie_id} not found in favorites"
        }), 404)

    user_favorites[username] = updated_favorites

    return make_response(jsonify({
        "status": "success",
        "message": f"Movie with ID {movie_id} removed from favorites"
    }), 200)

from catalog.utils.api_utils import search_movies
@movie_bp.route('/search-movies', methods=['GET'])
@login_required
def search_movies_route():
    """Search for movies from external API."""

    query = request.args.get('query')

    if not query:
        return make_response(jsonify({
            "status": "error",
            "message": "Query parameter is required"
        }), 400)

    try:
        # Call teammate's search helper
        results = search_movies(query)

        return make_response(jsonify({
            "status": "success",
            "results": results
        }), 200)

    except Exception as e:
        return make_response(jsonify({
            "status": "error",
            "message": "Failed to search movies",
            "details": str(e)
        }), 500)


@movie_bp.route('/get-movie/<int:movie_id>', methods=['GET'])
def get_movie(movie_id):
    """Retrieve movie details."""
    return jsonify({"message": f"get-movie route hit for ID {movie_id}"}), 200
