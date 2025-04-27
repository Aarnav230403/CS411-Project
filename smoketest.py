import requests

BASE_URL = "http://localhost:5001"

def run_smoketest():
    # Healthcheck
    health_response = requests.get(f"{BASE_URL}/api/health")
    assert health_response.status_code == 200
    print("Healthcheck passed")

    # Create user
    user_data = {"username": "testuser", "password": "testpassword"}
    create_user_response = requests.put(f"{BASE_URL}/api/create-user", json=user_data)
    print("Create user:", create_user_response.status_code, create_user_response.json())

    # Login
    session = requests.Session()
    login_response = session.post(f"{BASE_URL}/api/login", json=user_data)
    assert login_response.status_code == 200
    print("Login passed")

    # Add Favorite
    favorite_data = {"movie_id": "123", "movie_title": "Inception"}
    add_fav_response = session.post(f"{BASE_URL}/add-favorite", json=favorite_data)
    print("Add favorite:", add_fav_response.status_code, add_fav_response.json())

    # Get Favorites
    get_fav_response = session.get(f"{BASE_URL}/get-favorites")
    print("Get favorites:", get_fav_response.status_code, get_fav_response.json())

if __name__ == "__main__":
    run_smoketest()
