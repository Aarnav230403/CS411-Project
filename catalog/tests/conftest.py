import pytest
from app import create_app
from catalog.config import TestConfig
from catalog.db import db
from catalog.models.user_model import Users
from sqlalchemy.orm import scoped_session, sessionmaker

@pytest.fixture(scope="session")
def app():
    """Create and configure a new app instance for each test session."""
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
    """Returns a scoped session for tests."""
    with app.app_context():
        connection = db.engine.connect()
        transaction = connection.begin()
        options = dict(bind=connection, binds={})
        sess = scoped_session(sessionmaker(**options))
        db.session = sess
        yield sess
        transaction.rollback()
        connection.close()
        sess.remove()

@pytest.fixture(autouse=True)
def clear_users(session):
    """Automatically clears the users table before each test."""
    session.query(Users).delete()
    session.commit()
