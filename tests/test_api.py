import os
import pytest
from movie_api import search_movies, get_movie_details

# Before running these tests, make sure your TMDB_API_KEY is set in environment variables

def test_search_movies():
    results = search_movies("Inception")
    assert isinstance(results, list)
    assert any("Inception" in movie['title'] for movie in results)

def test_get_movie_details():
    # Using Inception's known TMDb ID = 27205 (You can verify this on TMDb site)
    movie = get_movie_details(27205)
    assert movie['title'] == "Inception"
