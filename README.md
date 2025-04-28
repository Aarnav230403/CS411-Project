# CS411-Project

🎬 Movie Dashboard
Overview
Movie Dashboard is a backend Flask application that enables users to create accounts, log in, manage their favorite movies, and search for movies using an external API.
It includes user authentication, SQLite database integration, a custom in-memory favorites model, and clean RESTful API design.

The project focuses on secure account management, API interaction, data persistence, and Docker containerization — simulating real-world backend development and legacy code management.

Technologies Used
Python 3.9

Flask

Flask-Login

Flask-SQLAlchemy

SQLite3

Docker

pytest for unit testing

External API (placeholder search functionality)

Setup Instructions
Clone the repository:

bash
Copy
Edit
git clone https://github.com/Aarnav230403/CS411-Project.git
cd CS411-Project
Set up virtual environment:

bash
Copy
Edit
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
Run the application:

bash
Copy
Edit
python app.py
App will start at http://localhost:5001

.env Template
Create a .env file in the root directory with at least:

bash
Copy
Edit
SECRET_KEY=your_secret_key_here
(Replace your_secret_key_here with a secure random string.)

API Routes
1. Health Check
Route: /api/health

Method: GET

Purpose: Verify the service is running

Response:

json
Copy
Edit
{
  "status": "success",
  "message": "Service is running"
}
2. Create User
Route: /api/create-user

Method: PUT

Purpose: Create a new user account

Request Body:

json
Copy
Edit
{
  "username": "your_username",
  "password": "your_password"
}
Response:

json
Copy
Edit
{
  "status": "success",
  "message": "User 'your_username' created successfully"
}
3. Login
Route: /api/login

Method: POST

Purpose: Authenticate a user and start a session

Request Body:

json
Copy
Edit
{
  "username": "your_username",
  "password": "your_password"
}
Response:

json
Copy
Edit
{
  "status": "success",
  "message": "User 'your_username' logged in successfully"
}
4. Logout
Route: /api/logout

Method: POST

Purpose: Logout the current user

Response:

json
Copy
Edit
{
  "status": "success",
  "message": "User logged out successfully"
}
5. Change Password
Route: /api/change-password

Method: POST

Purpose: Change the current user's password

Request Body:

json
Copy
Edit
{
  "new_password": "your_new_password"
}
Response:

json
Copy
Edit
{
  "status": "success",
  "message": "Password changed successfully"
}
6. Reset Users (for testing)
Route: /api/reset-users

Method: DELETE

Purpose: Deletes and recreates the user table

Response:

json
Copy
Edit
{
  "status": "success",
  "message": "Users table recreated successfully"
}
7. Add Favorite Movie
Route: /add-favorite

Method: POST

Purpose: Add a movie to the user's favorites list

Request Body:

json
Copy
Edit
{
  "movie_id": "123",
  "movie_title": "Inception"
}
Response:

json
Copy
Edit
{
  "status": "success",
  "message": "Movie 'Inception' added to favorites"
}
8. Get Favorite Movies
Route: /get-favorites

Method: GET

Purpose: Retrieve the list of a user's favorite movies

Response:

json
Copy
Edit
{
  "status": "success",
  "favorites": [
    {
      "movie_id": "123",
      "movie_title": "Inception"
    }
  ]
}
Testing
Unit Tests: Located in the tests/ folder (test_routes.py).

Smoke Test: smoketest.py validates user creation, login, and adding favorites.

Run tests with:

bash
Copy
Edit
pytest
✅ All tests are passing.

Docker
Build and run the container:

bash
Copy
Edit
docker build -t movie-dashboard .
docker run -p 5001:5001 movie-dashboard
Project Status
Core backend functionality is complete.

Fully dockerized.

All routes tested and passing smoketests.

