import uuid
import pytest
from catalog.models.user_model import Users

@pytest.fixture(autouse=True)
def isolate_user_data(session):
    """Ensure the users table is cleared and changes are rolled back after each test."""
    session.query(Users).delete()
    session.commit()
    yield
    session.query(Users).delete()
    session.commit()

@pytest.fixture
def sample_user():
    """Create a unique sample user for each test to avoid duplication."""
    random_username = f"testuser_{uuid.uuid4().hex[:6]}"
    return {
        "username": random_username,
        "password": "securepassword123"
    }

##########################################################
# User Creation
##########################################################

def test_create_user(session, sample_user):
    Users.create_user(**sample_user)
    user = session.query(Users).filter_by(username=sample_user["username"]).first()
    assert user is not None
    assert user.username == sample_user["username"]
    assert len(user.salt) == 32
    assert len(user.password) == 64

def test_create_duplicate_user(session, sample_user):
    Users.create_user(**sample_user)
    with pytest.raises(ValueError, match=f"User with username '{sample_user['username']}' already exists"):
        Users.create_user(**sample_user)

##########################################################
# User Authentication
##########################################################

def test_check_password_correct(session, sample_user):
    Users.create_user(**sample_user)
    assert Users.check_password(sample_user["username"], sample_user["password"]) is True

def test_check_password_incorrect(session, sample_user):
    Users.create_user(**sample_user)
    assert Users.check_password(sample_user["username"], "wrongpassword") is False

def test_check_password_user_not_found(session):
    with pytest.raises(ValueError, match="User nonexistentuser not found"):
        Users.check_password("nonexistentuser", "password")

##########################################################
# Update Password
##########################################################

def test_update_password(session, sample_user):
    Users.create_user(**sample_user)
    new_password = "newpassword456"
    Users.update_password(sample_user["username"], new_password)
    assert Users.check_password(sample_user["username"], new_password) is True

def test_update_password_user_not_found(session):
    with pytest.raises(ValueError, match="User nonexistentuser not found"):
        Users.update_password("nonexistentuser", "newpassword")

##########################################################
# Delete User
##########################################################

def test_delete_user(session, sample_user):
    Users.create_user(**sample_user)
    Users.delete_user(sample_user["username"])
    user = session.query(Users).filter_by(username=sample_user["username"]).first()
    assert user is None

def test_delete_user_not_found(session):
    with pytest.raises(ValueError, match="User nonexistentuser not found"):
        Users.delete_user("nonexistentuser")

##########################################################
# Get User
##########################################################

def test_get_id_by_username(session, sample_user):
    Users.create_user(**sample_user)
    user_id = Users.get_id_by_username(sample_user["username"])
    user = session.query(Users).filter_by(username=sample_user["username"]).first()
    assert user is not None
    assert user.id == user_id

def test_get_id_by_username_user_not_found(session):
    with pytest.raises(ValueError, match="User nonexistentuser not found"):
        Users.get_id_by_username("nonexistentuser")
