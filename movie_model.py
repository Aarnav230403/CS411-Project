# This will act as your in-memory database
favorites = {}

def add_favorite(user_id, movie):
    """Add a movie to a user's favorites."""
    if user_id not in favorites:
        favorites[user_id] = []
    favorites[user_id].append(movie)

def remove_favorite(user_id, movie_id):
    """Remove a movie from a user's favorites."""
    if user_id in favorites:
        favorites[user_id] = [
            movie for movie in favorites[user_id]
            if movie.get('id') != movie_id
        ]

def get_favorites(user_id):
    """Get all favorite movies for a user."""
    return favorites.get(user_id, [])

