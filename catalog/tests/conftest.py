import pytest

from app import create_app
from config import TestConfig
from catalog.models.user_model import Users  # optional depending on your tests
from catalog.sql.create_db import db  # <-- Make sure this is right path to your db object

@pytest.fixture
def app():
    app = create_app(config_class=TestConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def session(app):
    with app.app_context():
        yield db.session
