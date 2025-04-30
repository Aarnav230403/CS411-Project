import pytest
import os
from dotenv import load_dotenv
from movie_api import search_movies, get_movie_details

load_dotenv()
TMDB_API_KEY = os.getenv("TMDB_API_KEY")

@pytest.mark.skipif(not TMDB_API_KEY, reason="TMDB_API_KEY not set")
def test_search_movies():
    results = search_movies("Inception")
    assert isinstance(results, list)
    assert any("Inception" in movie['title'] for movie in results)

@pytest.mark.skipif(not TMDB_API_KEY, reason="TMDB_API_KEY not set")
def test_get_movie_details():
    movie = get_movie_details(27205)
    assert movie['title'] == "Inception"