import pytest
from app import create_app
from catalog.config import TestConfig
from catalog.db import db
from catalog.models.user_model import Users  # make sure it's imported

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

@pytest.fixture(autouse=True)
def clear_users(session):
    """Automatically clear the users table before every test."""
    session.query(Users).delete()
    session.commit()
