import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from app import create_app
from routes.movie_routes import user_favorites
from playlist.db import db
from config import TestingConfig

@pytest.fixture
def app_instance():
    app = create_app(config_class=TestingConfig)
    app.config['TESTING'] = True

    with app.app_context():
        db.create_all()
        yield app   # 🔥 yield app, NOT client!

@pytest.fixture
def client(app_instance):
    return app_instance.test_client()

@pytest.fixture
def auth(client):
    class AuthActions:
        def login(self, username="testuser", password="testpassword"):
            client.put('/api/create-user', json={
                "username": username,
                "password": password
            })
            client.post('/api/login', json={
                "username": username,
                "password": password
            })

        def logout(self):
            client.post('/api/logout')

    return AuthActions()

def test_healthcheck(client):
    """Test healthcheck endpoint."""
    response = client.get('/api/health')
    assert response.status_code == 200
    assert response.get_json() == {
        "status": "success",
        "message": "Service is running"
    }

def test_add_favorite(client, auth):
    """Test adding a favorite movie."""
    user_favorites.clear()
    auth.login()

    response = client.post('/add-favorite', json={
        "movie_id": "123",
        "movie_title": "Inception"
    })

    assert response.status_code == 201
    data = response.get_json()
    assert data["status"] == "success"
    assert "Movie 'Inception' added to favorites" in data["message"]

def test_get_favorites(client, auth):
    """Test retrieving favorite movies."""
    user_favorites.clear()
    auth.login()

    # First, add a favorite
    client.post('/add-favorite', json={
        "movie_id": "123",
        "movie_title": "Inception"
    })

    # Now, get favorites
    response = client.get('/get-favorites')

    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "success"
    assert isinstance(data["favorites"], list)
    assert len(data["favorites"]) == 1
    assert data["favorites"][0]["movie_id"] == "123"
    assert data["favorites"][0]["movie_title"] == "Inception"

def test_delete_favorite(client, auth):
    """Test deleting a favorite movie."""

    user_favorites.clear()  

    auth.login()

    # Add a favorite
    client.post('/add-favorite', json={
        "movie_id": "123",
        "movie_title": "Inception"
    })

    # Delete the favorite
    response = client.delete('/delete-favorite', json={
        "movie_id": "123"
    })

    # Assert successful deletion
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "success"
    assert "removed from favorites" in data["message"]

    favorites_response = client.get('/get-favorites')
    favorites_data = favorites_response.get_json()
    assert favorites_data["favorites"] == []

from unittest.mock import patch

def test_search_movies(client, auth):
    """Test searching for movies."""

    user_favorites.clear()  

    auth.login()

    # Patch the external search_movies function to return fake data
    with patch('routes.movie_routes.search_movies') as mock_search:
        mock_search.return_value = [
            {"movie_id": "1", "movie_title": "Inception"},
            {"movie_id": "2", "movie_title": "Interstellar"}
        ]

        response = client.get('/search-movies?query=inception')

        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "success"
        assert isinstance(data["results"], list)
        assert len(data["results"]) == 2
        assert data["results"][0]["movie_title"] == "Inception"
