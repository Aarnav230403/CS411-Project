import uuid
import pytest
from catalog.models.user_model import Users
from catalog.db import db


@pytest.fixture(autouse=True)
def clean_users_table(session):
    """Automatically clear users table before each test."""
    session.query(Users).delete()
    db.session.commit()


##########################################################
# User Creation
##########################################################

def test_create_user(session):
    username = f"testuser_{uuid.uuid4().hex[:6]}"
    password = "securepassword123"
    Users.create_user(username=username, password=password)
    user = session.query(Users).filter_by(username=username).first()
    assert user is not None
    assert user.username == username
    assert len(user.salt) == 32
    assert len(user.password) == 64

def test_create_duplicate_user(session):
    username = f"duplicate_{uuid.uuid4().hex[:6]}"
    password = "securepassword123"
    Users.create_user(username=username, password=password)
    with pytest.raises(ValueError, match=f"User with username '{username}' already exists"):
        Users.create_user(username=username, password=password)

##########################################################
# User Authentication
##########################################################

def test_check_password_correct(session):
    username = f"testuser_{uuid.uuid4().hex[:6]}"
    password = "securepassword123"
    Users.create_user(username=username, password=password)
    assert Users.check_password(username, password) is True

def test_check_password_incorrect(session):
    username = f"testuser_{uuid.uuid4().hex[:6]}"
    Users.create_user(username=username, password="securepassword123")
    assert Users.check_password(username, "wrongpassword") is False

def test_check_password_user_not_found(session):
    with pytest.raises(ValueError, match="User nonexistentuser not found"):
        Users.check_password("nonexistentuser", "password")

##########################################################
# Update Password
##########################################################

def test_update_password(session):
    username = f"testuser_{uuid.uuid4().hex[:6]}"
    Users.create_user(username=username, password="oldpassword")
    Users.update_password(username, "newpassword456")
    assert Users.check_password(username, "newpassword456") is True

def test_update_password_user_not_found(session):
    with pytest.raises(ValueError, match="User nonexistentuser not found"):
        Users.update_password("nonexistentuser", "newpassword")

##########################################################
# Delete User
##########################################################

def test_delete_user(session):
    username = f"testuser_{uuid.uuid4().hex[:6]}"
    Users.create_user(username=username, password="password")
    Users.delete_user(username)
    user = session.query(Users).filter_by(username=username).first()
    assert user is None

def test_delete_user_not_found(session):
    with pytest.raises(ValueError, match="User nonexistentuser not found"):
        Users.delete_user("nonexistentuser")

##########################################################
# Get User
##########################################################

def test_get_id_by_username(session):
    username = f"testuser_{uuid.uuid4().hex[:6]}"
    Users.create_user(username=username, password="password")
    user_id = Users.get_id_by_username(username)
    user = session.query(Users).filter_by(username=username).first()
    assert user is not None
    assert user.id == user_id

def test_get_id_by_username_user_not_found(session):
    with pytest.raises(ValueError, match="User nonexistentuser not found"):
        Users.get_id_by_username("nonexistentuser")
