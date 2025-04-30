import uuid
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from app import create_app
from routes.movie_routes import user_favorites
from catalog.db import db
from config import TestingConfig
from unittest.mock import patch

@pytest.fixture
def app_instance():
    app = create_app(config_class=TestingConfig)
    app.config['TESTING'] = True

    with app.app_context():
        db.drop_all()
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app_instance):
    return app_instance.test_client()

@pytest.fixture
def auth(client):
    class AuthActions:
        def login(self, username=None, password="testpassword"):
            if not username:
                username = f"testuser_{uuid.uuid4().hex[:6]}"
            client.put('/api/create-user', json={
                "username": username,
                "password": password
            })
            client.post('/api/login', json={
                "username": username,
                "password": password
            })
            return username

        def logout(self):
            client.post('/api/logout')

    return AuthActions()

@pytest.fixture(autouse=True)
def reset_favorites():
    user_favorites.clear()

def test_healthcheck(client):
    response = client.get('/api/health')
    assert response.status_code == 200
    assert response.get_json() == {
        "status": "success",
        "message": "Service is running"
    }

def test_add_favorite(client, auth):
    username = auth.login()
    response = client.post('/api/add-favorite', json={
        "movie_id": "123",
        "movie_title": "Inception"
    })
    assert response.status_code == 201
    data = response.get_json()
    assert data["status"] == "success"
    assert "Movie 'Inception' added to favorites" in data["message"]

def test_get_favorites(client, auth):
    username = auth.login()
    client.post('/api/add-favorite', json={
        "movie_id": "123",
        "movie_title": "Inception"
    })
    response = client.get('/api/get-favorites')
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "success"
    assert len(data["favorites"]) == 1
    assert data["favorites"][0]["movie_id"] == "123"

def test_delete_favorite(client, auth):
    username = auth.login()
    client.post('/api/add-favorite', json={
        "movie_id": "123",
        "movie_title": "Inception"
    })
    response = client.delete('/api/delete-favorite', json={"movie_id": "123"})
    assert response.status_code == 200
    assert "removed from favorites" in response.get_json()["message"]

    check_response = client.get('/api/get-favorites')
    assert check_response.get_json()["favorites"] == []

def test_search_movies(client, auth):
    auth.login()
    with patch('routes.movie_routes.search_movies') as mock_search:
        mock_search.return_value = [
            {"movie_id": "1", "movie_title": "Inception"},
            {"movie_id": "2", "movie_title": "Interstellar"}
        ]
        response = client.get('/api/search-movies?query=inception')
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "success"
        assert len(data["results"]) == 2
