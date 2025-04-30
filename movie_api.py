from dotenv import load_dotenv
import os
load_dotenv()


import requests
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# TMDb API Key (you should load it from your environment or config)
api_key = os.getenv("TMDB_API_KEY")

# Base URL
BASE_URL = 'https://api.themoviedb.org/3'


def search_movies(query):
    """Search for movies by query string."""
    logger.info(f"Searching movies with query: {query}")
    url = f"{BASE_URL}/search/movie"
    params = {
        'api_key': TMDB_API_KEY,
        'query': query
    }
    response = requests.get(url, params=params)
    response.raise_for_status()  # raise exception for bad responses
    return response.json().get('results', [])


def get_movie_details(movie_id):
    """Fetch detailed information about a movie by ID."""
    logger.info(f"Fetching details for movie ID: {movie_id}")
    url = f"{BASE_URL}/movie/{movie_id}"
    params = {
        'api_key': TMDB_API_KEY
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()
