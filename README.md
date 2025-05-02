CS411 Project ReadME
Overview

Our product is a RESTful web service that lets users sign up, log in, and manage their own movie collection. Once authenticated, a user can add new movies with title, year, genre and duration, remove or browse existing entries, and build a personal catalog of any subset of those movies. The catalog supports playback actions—play the current item, play the rest or the entire list, rewind back to the first movie, skip to a specific or random movie—and also lets users reorder entries (move to front/end, swap positions, or jump to a given slot). Every play action increments a movie’s play count, and you can retrieve stats like total catalog length, total duration, or a leaderboard of most-played films. All interactions happen over clean JSON endpoints with consistent success/error responses and HTTP status codes.

Environment Configuration
 Our product starts by reading a simple .env file for settings like the database URL, Flask secret key, debug flag and any other environment-specific values. The dotenv library loads those into memory so that the ProductionConfig class in config.py can pull them into app.config under keys such as SQLALCHEMY_DATABASE_URI, SECRET_KEY and FLASK_DEBUG.

Logger Setup
A small utility in catalog/utils/logger.py wraps Python’s built-in logger to add timestamps and log levels (INFO, WARNING, ERROR). Calling configure_logger(app.logger) in create_app() ensures every route and database action emits consistent, searchable logs.

Database Initialization
In catalog/db.py there is a single SQLAlchemy instance. Inside the application factory we call db.init_app(app) and then, within app.app_context(), run db.create_all() so that the Users, Movies and Catalog tables exist before handling any requests.
Models
Users has fields for username, hashed password, salt and pinCode. It handles creating new users by generating a random salt and storing the SHA-256 hash of password plus salt, checking passwords during login and updating passwords.
 Movies has fields for id, title, year, genre, duration and play_count. It provides methods to create movies, look up movies by ID or by title and year, list all or random movies, sort by play count and reset or delete the entire table.
 CatalogModel movies each user’s personal catalog order and current position. It supports adding and removing movies from a user’s catalog, clearing the catalog, playing the current movie, playing the rest or the entire catalog, rewinding to the first movie, jumping to a specific or random movie, moving or swapping entries, calculating the total number of movies and the combined duration, and incrementing play counts.


Authentication & Session Management
Flask-Login is used to manage user sessions. A user_loader callback fetches a Users record by its ID. The login route hashes the submitted password with the stored salt and, if it matches, calls login_user() to set a session cookie. The logout route calls logout_user(). All routes that modify movies or catalogs are decorated with @login_required so only authenticated users can access them.


Routes in app.py
The main application file handles the health check at /api/health and user management endpoints at /api/create-user, /api/login, /api/logout, /api/change-password and /api/reset-users. The change-password route requires an active session; the others do not. All routes briefly details can be found on the last pages of the document.


Movie Blueprint
All other endpoints live in the movie blueprint in routes/movie_routes.py and are mounted under /api. The movie CRUD operations include /api/create-movie, /api/delete-movie/ID, /api/get-all-movies, /api/get-movie-by-id/ID, /api/get-movie-by-compound-key, /api/get-random-movie and /api/reset-movies. Catalog operations include /api/add-movie-to-catalog, /api/remove-movie-from-catalog and /api/clear-catalog. Playback controls include /api/play-current-movie, /api/play-entire-catalog, /api/play-rest-of-catalog, /api/rewind-catalog, /api/go-to-movie-number/movie_NUMBER and /api/go-to-random-movie. Reordering routes include /api/move-movie-to-beginning, /api/move-movie-to-end, /api/move-movie-to-movie-number and /api/swap-movies-in-catalog. Stats and leaderboard endpoints are /api/get-catalog-length-duration and /api/movie-leaderboard.

Error Handling & Responses
All failures return a JSON object with status “error” and a descriptive message. HTTP status codes are used consistently: 400 for bad input, 401 for unauthorized, 404 for not found and 500 for server errors. Successful calls return status “success” with any requested data or confirmation message.

Running the Product
To run the product, populate our .env file, then start the app with either
 export FLASK_APP=app.py
 flask run
 or simply
 python app.py
 Clients like curl or Postman can then be used to interact with the endpoints described above.



Movie Routes



Below is a detailed look at every endpoint in the movie blueprint, with method, URL, inputs and outputs:
Create Movie
 Method: POST
 URL: /api/create-movie
 Requires login.
 Input (JSON):
 • title (string) – the movie’s title
 • year (integer) – release year
 • genre (string) – genre name
 • duration (integer) – length in seconds
 Success (201):
 • { status: "success", message: "Movie '<title>' added successfully" }
 Client errors (400):
 • missing fields
 • wrong data types
 Server error (500) on unexpected failure.
Delete Movie
Method: DELETE
 URL: /api/delete-movie/<movie_id>
 Requires login.
 Path parameter: movie_id (integer)
 Success (200):
 • { status: "success", message: "Movie with ID <movie_id> deleted successfully" }
 Client error (400) if movie not found, server error (500) on failure.
List All Movies
Method: GET
 URL: /api/get-all-movies-from-catalog?sort_by_play_count=<true|false>
 Requires login.
 Query parameter (optional):
 • sort_by_play_count=true sorts descending by play count
 Success (200):
 • { status: "success", message: "Movies retrieved successfully", movies: [ …movie objects… ] }
 Server error (500) on failure.
Get Movie by ID
Method: GET
 URL: /api/get-movie-from-catalog-by-id/<movie_id>
 Requires login.
 Path parameter: movie_id (integer)
 Success (200):
 • { status: "success", message: "Movie retrieved successfully", movie: { id, title, year, genre, duration, play_count } }
 Client error (400) if not found, server error (500) otherwise.
Get Movie by Compound Key
Method: GET
 URL: /api/get-movie-from-catalog-by-compound-key?title=<title>&year=<year>
 Requires login.
 Query parameters: title (string), year (integer)
 Success (200): same payload as Get Movie by ID.
 Client error (400) if missing or invalid parameters or not found.

Get Random Movie
Method: GET
 URL: /api/get-random-movie
 Requires login.
 Success (200):
 • { status: "success", message: "Random movie retrieved successfully", movie: { … } }
 Client error (400) if catalog empty, server error (500) on failure.
Reset Movies Table
Method: DELETE
 URL: /api/reset-movies
 No login required.
 Drops and recreates the movies table.
 Success (200):
 • { status: "success", message: "Movies table recreated successfully" }
 Server error (500) on failure.

Add Movie to Catalog

 Method: POST
 URL: /api/add-movie-to-catalog
 Requires login.
 Input (JSON): title (string), year (integer)
 Success (201):
 • { status: "success", message: "Movie '<title>' (<year>) added to catalog" }
 Client errors (400) if fields missing, invalid year or movie not found.
Remove Movie from Catalog
Method: DELETE
 URL: /api/remove-movie-from-catalog
 Requires login.
 Input (JSON): title (string), year (integer)
 Success (200):
 • { status: "success", message: "Movie '<title>' (<year>) removed from catalog" }
 Client error (400) on missing fields or movie not in catalog.
Clear Catalog
 Method: POST
 URL: /api/clear-catalog
 Requires login.
 Removes all entries from the current user’s catalog.
 Success (200):
 • { status: "success", message: "Catalog cleared" }
 Server error (500) on failure.
Playback Controls
All require login.
 play-current-movie (POST /api/play-current-movie)
 • Marks the current movie as played (incrementing its play count) and returns its details.
 play-entire-catalog (POST /api/play-entire-catalog)
 • Plays through every movie in order.
 play-rest-of-catalog (POST /api/play-rest-of-catalog)
 • Plays from current movie to the end.
 rewind-catalog (POST /api/rewind-catalog)
 • Sets current movie back to the first movie.
 go-to-movie-number (POST /api/go-to-movie-number/<movie_number>)
 • Jumps to the specified zero-based movie.
 go-to-random-movie (POST /api/go-to-random-movie)
 • Picks and jumps to a random movie.
Reordering
All require login.
 move-movie-to-beginning (POST /api/move-movie-to-beginning)
 • Input (JSON): title, year
 • Moves that movie to the front of the catalog.
 move-movie-to-end (POST /api/move-movie-to-end)
 • Input (JSON): title, year
 move-movie-to-movie-number (POST /api/move-movie-to-movie-number)
 • Input (JSON): title, year, movie_number
 swap-movies-in-catalog (POST /api/swap-movies-in-catalog)
 • Input (JSON): movie_number_1, movie_number_2
 • Swaps the positions of the two specified movies.
Statistics & Leaderboard
 get-catalog-length-duration (GET /api/get-catalog-length-duration)
 • Requires login. Returns JSON with catalog_length (count) and catalog_duration (seconds).
 movie-leaderboard (GET /api/movie-leaderboard)
 • No login required. Returns a list of all movies sorted by play_count descending.
Each route returns JSON with a “status” of “success” or “error,” a human-readable message, and any relevant data payload. HTTP status codes follow REST conventions: 200 OK, 201 Created, 400 Bad Request, 401 Unauthorized, 404 Not Found, 500 Internal Server Error.

