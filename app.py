from dotenv import load_dotenv
from flask import Flask, jsonify, make_response, Response, request
from flask_login import LoginManager, login_user, logout_user, login_required, current_user

from config import ProductionConfig

from catalog.db import db
from catalog.models.movie_model import Movies
from catalog.models.catalog_model import CatalogModel
from catalog.models.user_model import Users
from catalog.utils.logger import configure_logger


load_dotenv()

from routes.movie_routes import movie_bp



from dotenv import load_dotenv
from flask import Flask, jsonify, make_response, Response, request
from flask_login import LoginManager, login_user, logout_user, login_required, current_user

from config import ProductionConfig

from catalog.db import db
from catalog.models.movie_model import Movies
from catalog.models.catalog_model import CatalogModel
from catalog.models.user_model import Users
from catalog.utils.logger import configure_logger

load_dotenv()

from routes.movie_routes import movie_bp

def create_app(config_class=ProductionConfig) -> Flask:
    """Create a Flask application with the specified configuration.

    Args:
        config_class (Config): The configuration class to use.

    Returns:
        Flask app: The configured Flask application.

    """
    app = Flask(__name__)
    configure_logger(app.logger)

    app.config.from_object(config_class)

    # Initialize database
    db.init_app(app)
    with app.app_context():
        db.create_all()

    # Initialize login manager
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'

    @login_manager.user_loader
    def load_user(user_id):
        return Users.query.filter_by(username=user_id).first()

    @login_manager.unauthorized_handler
    def unauthorized():
        return make_response(jsonify({
            "status": "error",
            "message": "Authentication required"
        }), 401)

    catalog_model = CatalogModel()

    @app.route('/api/health', methods=['GET'])
    def healthcheck() -> Response:
        """Health check route to verify the service is running.

        Returns:
            JSON response indicating the health status of the service.

        """
        app.logger.info("Health check endpoint hit")
        return make_response(jsonify({
            'status': 'success',
            'message': 'Service is running'
        }), 200)
    

    if __name__ == '__main__':
        app = create_app()
        app.run(debug=True)


    ##########################################################
    #
    # User Management
    #
    ##########################################################

    @app.route('/api/create-user', methods=['PUT'])
    def create_user() -> Response:
        """Register a new user account.

        Expected JSON Input:
            - username (str): The desired username.
            - password (str): The desired password.
            - pinCode (str): A 4-digit pincode for added verification.

        Returns:
            JSON response indicating the success of the user creation.

        Raises:
            400 error if any required field is missing or invalid.
            500 error if there is an issue creating the user in the database.
        """
        try:
            data = request.get_json()
            username = data.get("username")
            password = data.get("password")
            pin_code = data.get("pinCode")

            if not username or not password or not pin_code:
                return make_response(jsonify({
                    "status": "error",
                    "message": "Username, password, and pinCode are required"
                }), 400)

            if not pin_code.isdigit() or len(pin_code) != 4:
                return make_response(jsonify({
                    "status": "error",
                    "message": "pinCode must be a 4-digit number"
                }), 400)

            Users.create_user(username, password, pin_code)

            return make_response(jsonify({
                "status": "success",
                "message": f"User '{username}' created successfully"
            }), 201)

        except ValueError as e:
            return make_response(jsonify({
                "status": "error",
                "message": str(e)
            }), 400)
        except Exception as e:
            app.logger.error(f"User creation failed: {e}")
            return make_response(jsonify({
                "status": "error",
                "message": "An internal error occurred while creating user",
                "details": str(e)
            }), 500)


    @app.route('/api/login', methods=['POST'])
    def login() -> Response:
        """Authenticate a user and log them in.

        Expected JSON Input:
            - username (str): The username of the user.
            - password (str): The password of the user.

        Returns:
            JSON response indicating the success of the login attempt.

        Raises:
            401 error if the username or password is incorrect.
        """
        try:
            data = request.get_json()
            username = data.get("username")
            password = data.get("password")

            if not username or not password:
                return make_response(jsonify({
                    "status": "error",
                    "message": "Username and password are required"
                }), 400)

            if Users.check_password(username, password):
                user = Users.query.filter_by(username=username).first()
                login_user(user)
                return make_response(jsonify({
                    "status": "success",
                    "message": f"User '{username}' logged in successfully"
                }), 200)
            else:
                return make_response(jsonify({
                    "status": "error",
                    "message": "Invalid username or password"
                }), 401)

        except ValueError as e:
            return make_response(jsonify({
                "status": "error",
                "message": str(e)
            }), 401)
        except Exception as e:
            app.logger.error(f"Login failed: {e}")
            return make_response(jsonify({
                "status": "error",
                "message": "An internal error occurred during login",
                "details": str(e)
            }), 500)

    @app.route('/api/logout', methods=['POST'])
    @login_required
    def logout() -> Response:
        """Log out the current user.

        Returns:
            JSON response indicating the success of the logout operation.

        """
        logout_user()
        return make_response(jsonify({
            "status": "success",
            "message": "User logged out successfully"
        }), 200)

    @app.route('/api/change-password', methods=['POST'])
    @login_required
    def change_password() -> Response:
        """Change the password for the current user.

        Expected JSON Input:
            - new_password (str): The new password to set.

        Returns:
            JSON response indicating the success of the password change.

        Raises:
            400 error if the new password is not provided.
            500 error if there is an issue updating the password in the database.
        """
        try:
            data = request.get_json()
            new_password = data.get("new_password")

            if not new_password:
                return make_response(jsonify({
                    "status": "error",
                    "message": "New password is required"
                }), 400)

            username = current_user.username
            Users.update_password(username, new_password)
            return make_response(jsonify({
                "status": "success",
                "message": "Password changed successfully"
            }), 200)

        except ValueError as e:
            return make_response(jsonify({
                "status": "error",
                "message": str(e)
            }), 400)
        except Exception as e:
            app.logger.error(f"Password change failed: {e}")
            return make_response(jsonify({
                "status": "error",
                "message": "An internal error occurred while changing password",
                "details": str(e)
            }), 500)

    @app.route('/api/reset-users', methods=['DELETE'])
    def reset_users() -> Response:
        """Recreate the users table to delete all users.

        Returns:
            JSON response indicating the success of recreating the Users table.

        Raises:
            500 error if there is an issue recreating the Users table.
        """
        try:
            app.logger.info("Received request to recreate Users table")
            with app.app_context():
                Users.__table__.drop(db.engine)
                Users.__table__.create(db.engine)
            app.logger.info("Users table recreated successfully")
            return make_response(jsonify({
                "status": "success",
                "message": f"Users table recreated successfully"
            }), 200)

        except Exception as e:
            app.logger.error(f"Users table recreation failed: {e}")
            return make_response(jsonify({
                "status": "error",
                "message": "An internal error occurred while deleting users",
                "details": str(e)
            }), 500)

    ##########################################################
    #
    # Movies
    #
    ##########################################################

    @app.route('/api/reset-movies', methods=['DELETE'])
    def reset_movies() -> Response:
        """Recreate the movies table to delete movies.

        Returns:
            JSON response indicating the success of recreating the Movies table.

        Raises:
            500 error if there is an issue recreating the Movies table.
        """
        try:
            app.logger.info("Received request to recreate Movies table")
            with app.app_context():
                Movies.__table__.drop(db.engine)
                Movies.__table__.create(db.engine)
            app.logger.info("Movies table recreated successfully")
            return make_response(jsonify({
                "status": "success",
                "message": f"Movies table recreated successfully"
            }), 200)

        except Exception as e:
            app.logger.error(f"Movies table recreation failed: {e}")
            return make_response(jsonify({
                "status": "error",
                "message": "An internal error occurred while deleting users",
                "details": str(e)
            }), 500)


    @app.route('/api/create-movie', methods=['POST'])
    @login_required
    def add_movie() -> Response:
        """Route to add a new movie to the catalog.

        Expected JSON Input:
            - title (str): The movie title.
            - year (int): The year the movie was released.
            - genre (str): The genre of the movie.
            - duration (int): The duration of the movie in seconds.

        Returns:
            JSON response indicating the success of the movie addition.

        Raises:
            400 error if input validation fails.
            500 error if there is an issue adding the movie to the catalog.

        """
        app.logger.info("Received request to add a new movie")

        try:
            data = request.get_json()

            required_fields = ["title", "year", "genre", "duration"]
            missing_fields = [field for field in required_fields if field not in data]

            if missing_fields:
                app.logger.warning(f"Missing required fields: {missing_fields}")
                return make_response(jsonify({
                    "status": "error",
                    "message": f"Missing required fields: {', '.join(missing_fields)}"
                }), 400)

            title = data["title"]
            year = data["year"]
            genre = data["genre"]
            duration = data["duration"]

            if (
                not isinstance(title, str)
                or not isinstance(year, int)
                or not isinstance(genre, str)
                or not isinstance(duration, int)
            ):
                app.logger.warning("Invalid input data types")
                return make_response(jsonify({
                    "status": "error",
                    "message": "Invalid input types: title/genre should be strings, year and duration should be integers"
                }), 400)

            app.logger.info(f"Adding movie: {title} ({year}), Genre: {genre}, Duration: {duration}s")
            Movies.create_movie(title=title, year=year, genre=genre, duration=duration)

            app.logger.info(f"Movie added successfully: {title}")
            return make_response(jsonify({
                "status": "success",
                "message": f"Movie '{title}' added successfully"
            }), 201)

        except Exception as e:
            app.logger.error(f"Failed to add movie: {e}")
            return make_response(jsonify({
                "status": "error",
                "message": "An internal error occurred while adding the movie",
                "details": str(e)
            }), 500)


    @app.route('/api/delete-movie/<int:movie_id>', methods=['DELETE'])
    @login_required
    def delete_movie(movie_id: int) -> Response:
        """Route to delete a movie by ID.

        Path Parameter:
            - movie_id (int): The ID of the movie to delete.

        Returns:
            JSON response indicating success of the operation.

        Raises:
            400 error if the movie does not exist.
            500 error if there is an issue removing the movie from the database.

        """
        try:
            app.logger.info(f"Received request to delete movie with ID {movie_id}")

            # Check if the movie exists before attempting to delete
            movie = Movies.get_movie_by_id(movie_id)
            if not movie:
                app.logger.warning(f"Movie with ID {movie_id} not found.")
                return make_response(jsonify({
                    "status": "error",
                    "message": f"Movie with ID {movie_id} not found"
                }), 400)

            Movies.delete_movie(movie_id)
            app.logger.info(f"Successfully deleted movie with ID {movie_id}")

            return make_response(jsonify({
                "status": "success",
                "message": f"Movie with ID {movie_id} deleted successfully"
            }), 200)

        except Exception as e:
            app.logger.error(f"Failed to delete movie: {e}")
            return make_response(jsonify({
                "status": "error",
                "message": "An internal error occurred while deleting the movie",
                "details": str(e)
            }), 500)


    @app.route('/api/get-all-movies-from-catalog', methods=['GET'])
    @login_required
    def get_all_movies() -> Response:
        """Route to retrieve all movies in the catalog (non-deleted), with an option to sort by play count.

        Query Parameter:
            - sort_by_play_count (bool, optional): If true, sort movies by play count.

        Returns:
            JSON response containing the list of movies.

        Raises:
            500 error if there is an issue retrieving movies from the catalog.

        """
        try:
            # Extract query parameter for sorting by play count
            sort_by_play_count = request.args.get('sort_by_play_count', 'false').lower() == 'true'

            app.logger.info(f"Received request to retrieve all movies from catalog (sort_by_play_count={sort_by_play_count})")

            movies = Movies.get_all_movies(sort_by_play_count=sort_by_play_count)

            app.logger.info(f"Successfully retrieved {len(movies)} movies from the catalog")

            return make_response(jsonify({
                "status": "success",
                "message": "Movies retrieved successfully",
                "movies": movies
            }), 200)

        except Exception as e:
            app.logger.error(f"Failed to retrieve movies: {e}")
            return make_response(jsonify({
                "status": "error",
                "message": "An internal error occurred while retrieving movies",
                "details": str(e)
            }), 500)


    @app.route('/api/get-movie-from-catalog-by-id/<int:movie_id>', methods=['GET'])
    @login_required
    def get_movie_by_id(movie_id: int) -> Response:
        """Route to retrieve a movie by its ID.

        Path Parameter:
            - movie_id (int): The ID of the movie.

        Returns:
            JSON response containing the movie details.

        Raises:
            400 error if the movie does not exist.
            500 error if there is an issue retrieving the movie.

        """
        try:
            app.logger.info(f"Received request to retrieve movie with ID {movie_id}")

            movie = Movies.get_movie_by_id(movie_id)
            if not movie:
                app.logger.warning(f"Movie with ID {movie_id} not found.")
                return make_response(jsonify({
                    "status": "error",
                    "message": f"Movie with ID {movie_id} not found"
                }), 400)

            app.logger.info(f"Successfully retrieved movie: {movie.title} (ID {movie_id})")

            return make_response(jsonify({
                "status": "success",
                "message": "Movie retrieved successfully",
                "movie": movie
            }), 200)

        except Exception as e:
            app.logger.error(f"Failed to retrieve movie by ID: {e}")
            return make_response(jsonify({
                "status": "error",
                "message": "An internal error occurred while retrieving the movie",
                "details": str(e)
            }), 500)


    @app.route('/api/get-movie-from-catalog-by-compound-key', methods=['GET'])
    @login_required
    def get_movie_by_compound_key() -> Response:
        """Route to retrieve a movie by its compound key (title, year).

        Query Parameters:
            - title (str): The movie title.
            - year (int): The year the movie was released.

        Returns:
            JSON response containing the movie details.

        Raises:
            400 error if required query parameters are missing or invalid.
            500 error if there is an issue retrieving the movie.

        """
        try:
            title = request.args.get('title')
            year = request.args.get('year')

            if not title or not year:
                app.logger.warning("Missing required query parameters: title, year")
                return make_response(jsonify({
                    "status": "error",
                    "message": "Missing required query parameters: title, year"
                }), 400)

            try:
                year = int(year)
            except ValueError:
                app.logger.warning(f"Invalid year format: {year}. Year must be an integer.")
                return make_response(jsonify({
                    "status": "error",
                    "message": "Year must be an integer"
                }), 400)

            app.logger.info(f"Received request to retrieve movie by compound key: {title}, {year}")

            movie = Movies.get_movie_by_compound_key(title, year)
            if not movie:
                app.logger.warning(f"Movie not found: {title} ({year})")
                return make_response(jsonify({
                    "status": "error",
                    "message": f"Movie not found: {title} ({year})"
                }), 400)

            app.logger.info(f"Successfully retrieved movie: {movie.title} ({year})")

            return make_response(jsonify({
                "status": "success",
                "message": "Movie retrieved successfully",
                "movie": movie
            }), 200)

        except Exception as e:
            app.logger.error(f"Failed to retrieve movie by compound key: {e}")
            return make_response(jsonify({
                "status": "error",
                "message": "An internal error occurred while retrieving the movie",
                "details": str(e)
            }), 500)


    @app.route('/api/get-random-movie', methods=['GET'])
    @login_required
    def get_random_movie() -> Response:
        """Route to retrieve a random movie from the catalog.

        Returns:
            JSON response containing the details of a random movie.

        Raises:
            400 error if no movies exist in the catalog.
            500 error if there is an issue retrieving the movie

        """
        try:
            app.logger.info("Received request to retrieve a random movie from the catalog")

            movie = Movies.get_random_movie()
            if not movie:
                app.logger.warning("No movies found in the catalog.")
                return make_response(jsonify({
                    "status": "error",
                    "message": "No movies available in the catalog"
                }), 400)

            app.logger.info(f"Successfully retrieved random movie: {movie.title}")

            return make_response(jsonify({
                "status": "success",
                "message": "Random movie retrieved successfully",
                "movie": movie
            }), 200)

        except Exception as e:
            app.logger.error(f"Failed to retrieve random movie: {e}")
            return make_response(jsonify({
                "status": "error",
                "message": "An internal error occurred while retrieving a random movie",
                "details": str(e)
            }), 500)


    ############################################################
    #
    # Catalog Add / Remove
    #
    ############################################################


    @app.route('/api/add-movie-to-catalog', methods=['POST'])
    @login_required
    def add_movie_to_catalog() -> Response:
        """Route to add a movie to the catalog by compound key (title, year).

        Expected JSON Input:
            - title (str): The movie title.
            - year (int): The year the movie was released.

        Returns:
            JSON response indicating success of the addition.

        Raises:
            400 error if required fields are missing or the movie does not exist.
            500 error if there is an issue adding the movie to the catalog.

        """
        try:
            app.logger.info("Received request to add movie to catalog")

            data = request.get_json()
            required_fields = ["title", "year"]
            missing_fields = [field for field in required_fields if field not in data]

            if missing_fields:
                app.logger.warning(f"Missing required fields: {missing_fields}")
                return make_response(jsonify({
                    "status": "error",
                    "message": f"Missing required fields: {', '.join(missing_fields)}"
                }), 400)

            title = data["title"]

            try:
                year = int(data["year"])
            except ValueError:
                app.logger.warning(f"Invalid year format: {data['year']}")
                return make_response(jsonify({
                    "status": "error",
                    "message": "Year must be a valid integer"
                }), 400)

            app.logger.info(f"Looking up movie: {title} ({year})")
            movie = Movies.get_movie_by_compound_key(title, year)

            if not movie:
                app.logger.warning(f"Movie not found: {title} ({year})")
                return make_response(jsonify({
                    "status": "error",
                    "message": f"Movie '{title}' ({year}) not found in catalog"
                }), 400)

            catalog_model.add_movie_to_catalog(movie)
            app.logger.info(f"Successfully added movie to catalog: {title} ({year})")

            return make_response(jsonify({
                "status": "success",
                "message": f"Movie '{title}' ({year}) added to catalog"
            }), 201)

        except Exception as e:
            app.logger.error(f"Failed to add movie to catalog: {e}")
            return make_response(jsonify({
                "status": "error",
                "message": "An internal error occurred while adding the movie to the catalog",
                "details": str(e)
            }), 500)


    @app.route('/api/remove-movie-from-catalog', methods=['DELETE'])
    @login_required
    def remove_movie_by_movie_id() -> Response:
        """Route to remove a movie from the catalog by compound key (title, year).

        Expected JSON Input:
            - title (str): The movie title.
            - year (int): The year the movie was released.

        Returns:
            JSON response indicating success of the removal.

        Raises:
            400 error if required fields are missing or the movie does not exist in the catalog.
            500 error if there is an issue removing the movie.

        """
        try:
            app.logger.info("Received request to remove movie from catalog")

            data = request.get_json()
            required_fields = ["title", "year"]
            missing_fields = [field for field in required_fields if field not in data]

            if missing_fields:
                app.logger.warning(f"Missing required fields: {missing_fields}")
                return make_response(jsonify({
                    "status": "error",
                    "message": f"Missing required fields: {', '.join(missing_fields)}"
                }), 400)

            title = data["title"]

            try:
                year = int(data["year"])
            except ValueError:
                app.logger.warning(f"Invalid year format: {data['year']}")
                return make_response(jsonify({
                    "status": "error",
                    "message": "Year must be a valid integer"
                }), 400)

            app.logger.info(f"Looking up movie to remove: {title} ({year})")
            movie = Movies.get_movie_by_compound_key(title, year)

            if not movie:
                app.logger.warning(f"Movie not found in catalog: {title} ({year})")
                return make_response(jsonify({
                    "status": "error",
                    "message": f"Movie '{title}' ({year}) not found in catalog"
                }), 400)

            catalog_model.remove_movie_by_movie_id(movie.id)
            app.logger.info(f"Successfully removed movie from catalog: {title} ({year})")

            return make_response(jsonify({
                "status": "success",
                "message": f"Movie '{title}' ({year}) removed from catalog"
            }), 200)

        except Exception as e:
            app.logger.error(f"Failed to remove movie from catalog: {e}")
            return make_response(jsonify({
                "status": "error",
                "message": "An internal error occurred while removing the movie from the catalog",
                "details": str(e)
            }), 500)


    @app.route('/api/remove-movie-from-catalog-by-track-number/<int:track_number>', methods=['DELETE'])
    @login_required
    def remove_movie_by_track_number(track_number: int) -> Response:
        """Route to remove a movie from the catalog by track number.

        Path Parameter:
            - track_number (int): The track number of the movie to remove.

        Returns:
            JSON response indicating success of the removal.

        Raises:
            404 error if the track number does not exist.
            500 error if there is an issue removing the movie.

        """
        try:
            app.logger.info(f"Received request to remove movie at track number {track_number} from catalog")

            catalog_model.remove_movie_by_track_number(track_number)

            app.logger.info(f"Successfully removed movie at track number {track_number} from catalog")
            return make_response(jsonify({
                "status": "success",
                "message": f"Movie at track number {track_number} removed from catalog"
            }), 200)

        except ValueError as e:
            app.logger.warning(f"Track number {track_number} not found in catalog: {e}")
            return make_response(jsonify({
                "status": "error",
                "message": f"Track number {track_number} not found in catalog"
            }), 404)

        except Exception as e:
            app.logger.error(f"Failed to remove movie at track number {track_number}: {e}")
            return make_response(jsonify({
                "status": "error",
                "message": "An internal error occurred while removing the movie from the catalog",
                "details": str(e)
            }), 500)


    @app.route('/api/clear-catalog', methods=['POST'])
    @login_required
    def clear_catalog() -> Response:
        """Route to clear all movies from the catalog.

        Returns:
            JSON response indicating success of the operation.

        Raises:
            500 error if there is an issue clearing the catalog.

        """
        try:
            app.logger.info("Received request to clear the catalog")

            catalog_model.clear_catalog()

            app.logger.info("Successfully cleared the catalog")
            return make_response(jsonify({
                "status": "success",
                "message": "Catalog cleared"
            }), 200)

        except Exception as e:
            app.logger.error(f"Failed to clear catalog: {e}")
            return make_response(jsonify({
                "status": "error",
                "message": "An internal error occurred while clearing the catalog",
                "details": str(e)
            }), 500)


    ############################################################
    #
    # Play Catalog
    #
    ############################################################


    @app.route('/api/play-current-movie', methods=['POST'])
    @login_required
    def play_current_movie() -> Response:
        """Route to play the current movie in the catalog.

        Returns:
            JSON response indicating success of the operation.

        Raises:
            404 error if there is no current movie.
            500 error if there is an issue playing the current movie.

        """
        try:
            app.logger.info("Received request to play the current movie")

            current_movie = catalog_model.get_current_movie()
            if not current_movie:
                app.logger.warning("No current movie found in the catalog")
                return make_response(jsonify({
                    "status": "error",
                    "message": "No current movie found in the catalog"
                }), 404)

            catalog_model.play_current_movie()
            app.logger.info(f"Now playing: {current_movie.title} ({current_movie.year})")

            return make_response(jsonify({
                "status": "success",
                "message": "Now playing current movie",
                "movie": {
                    "id": current_movie.id,
                    "title": current_movie.title,
                    "year": current_movie.year,
                    "genre": current_movie.genre,
                    "duration": current_movie.duration
                }
            }), 200)

        except Exception as e:
            app.logger.error(f"Failed to play current movie: {e}")
            return make_response(jsonify({
                "status": "error",
                "message": "An internal error occurred while playing the current movie",
                "details": str(e)
            }), 500)


    @app.route('/api/play-entire-catalog', methods=['POST'])
    @login_required
    def play_entire_catalog() -> Response:
        """Route to play all movies in the catalog.

        Returns:
            JSON response indicating success of the operation.

        Raises:
            400 error if the catalog is empty.
            500 error if there is an issue playing the catalog.

        """
        try:
            app.logger.info("Received request to play the entire catalog")

            if catalog_model.check_if_empty():
                app.logger.warning("Cannot play catalog: No movies available")
                return make_response(jsonify({
                    "status": "error",
                    "message": "Cannot play catalog: No movies available"
                }), 400)

            catalog_model.play_entire_catalog()
            app.logger.info("Playing entire catalog")

            return make_response(jsonify({
                "status": "success",
                "message": "Playing entire catalog"
            }), 200)

        except Exception as e:
            app.logger.error(f"Failed to play entire catalog: {e}")
            return make_response(jsonify({
                "status": "error",
                "message": "An internal error occurred while playing the catalog",
                "details": str(e)
            }), 500)


    @app.route('/api/play-rest-of-catalog', methods=['POST'])
    @login_required
    def play_rest_of_catalog() -> Response:
        """Route to play the rest of the catalog from the current track.

        Returns:
            JSON response indicating success of the operation.

        Raises:
            400 error if the catalog is empty or if no current movie is playing.
            500 error if there is an issue playing the rest of the catalog.

        """
        try:
            app.logger.info("Received request to play the rest of the catalog")

            if catalog_model.check_if_empty():
                app.logger.warning("Cannot play rest of catalog: No movies available")
                return make_response(jsonify({
                    "status": "error",
                    "message": "Cannot play rest of catalog: No movies available"
                }), 400)

            if not catalog_model.get_current_movie():
                app.logger.warning("No current movie playing. Cannot continue catalog.")
                return make_response(jsonify({
                    "status": "error",
                    "message": "No current movie playing. Cannot continue catalog."
                }), 400)

            catalog_model.play_rest_of_catalog()
            app.logger.info("Playing rest of the catalog")

            return make_response(jsonify({
                "status": "success",
                "message": "Playing rest of the catalog"
            }), 200)

        except Exception as e:
            app.logger.error(f"Failed to play rest of the catalog: {e}")
            return make_response(jsonify({
                "status": "error",
                "message": "An internal error occurred while playing the rest of the catalog",
                "details": str(e)
            }), 500)


    @app.route('/api/rewind-catalog', methods=['POST'])
    @login_required
    def rewind_catalog() -> Response:
        """Route to rewind the catalog to the first movie.

        Returns:
            JSON response indicating success of the operation.

        Raises:
            400 error if the catalog is empty.
            500 error if there is an issue rewinding the catalog.

        """
        try:
            app.logger.info("Received request to rewind the catalog")

            if catalog_model.check_if_empty():
                app.logger.warning("Cannot rewind: No movies in catalog")
                return make_response(jsonify({
                    "status": "error",
                    "message": "Cannot rewind: No movies in catalog"
                }), 400)

            catalog_model.rewind_catalog()
            app.logger.info("Catalog successfully rewound to the first movie")

            return make_response(jsonify({
                "status": "success",
                "message": "Catalog rewound to the first movie"
            }), 200)

        except Exception as e:
            app.logger.error(f"Failed to rewind catalog: {e}")
            return make_response(jsonify({
                "status": "error",
                "message": "An internal error occurred while rewinding the catalog",
                "details": str(e)
            }), 500)


    @app.route('/api/go-to-track-number/<int:track_number>', methods=['POST'])
    @login_required
    def go_to_track_number(track_number: int) -> Response:
        """Route to set the catalog to start playing from a specific track number.

        Path Parameter:
            - track_number (int): The track number to set as the current movie.

        Returns:
            JSON response indicating success or an error message.

        Raises:
            400 error if the track number is invalid.
            500 error if there is an issue updating the track number.
        """
        try:
            app.logger.info(f"Received request to go to track number {track_number}")

            if not catalog_model.is_valid_track_number(track_number):
                app.logger.warning(f"Invalid track number: {track_number}")
                return make_response(jsonify({
                    "status": "error",
                    "message": f"Invalid track number: {track_number}. Please provide a valid track number."
                }), 400)

            catalog_model.go_to_track_number(track_number)
            app.logger.info(f"Catalog set to track number {track_number}")

            return make_response(jsonify({
                "status": "success",
                "message": f"Now playing from track number {track_number}"
            }), 200)

        except ValueError as e:
            app.logger.warning(f"Failed to set track number {track_number}: {e}")
            return make_response(jsonify({
                "status": "error",
                "message": str(e)
            }), 400)

        except Exception as e:
            app.logger.error(f"Internal error while going to track number {track_number}: {e}")
            return make_response(jsonify({
                "status": "error",
                "message": "An internal error occurred while changing the track number",
                "details": str(e)
            }), 500)


    @app.route('/api/go-to-random-track', methods=['POST'])
    @login_required
    def go_to_random_track() -> Response:
        """Route to set the catalog to start playing from a random track number.

        Returns:
            JSON response indicating success or an error message.

        Raises:
            400 error if the catalog is empty.
            500 error if there is an issue selecting a random track.

        """
        try:
            app.logger.info("Received request to go to a random track")

            if catalog_model.get_catalog_length() == 0:
                app.logger.warning("Attempted to go to a random track but the catalog is empty")
                return make_response(jsonify({
                    "status": "error",
                    "message": "Cannot select a random track. The catalog is empty."
                }), 400)

            catalog_model.go_to_random_track()
            app.logger.info(f"Catalog set to random track number {catalog_model.current_track_number}")

            return make_response(jsonify({
                "status": "success",
                "message": f"Now playing from random track number {catalog_model.current_track_number}"
            }), 200)

        except Exception as e:
            app.logger.error(f"Internal error while selecting a random track: {e}")
            return make_response(jsonify({
                "status": "error",
                "message": "An internal error occurred while selecting a random track",
                "details": str(e)
            }), 500)


    ############################################################
    #
    # View Catalog
    #
    ############################################################


    @app.route('/api/get-all-movies-from-catalog', methods=['GET'])
    @login_required
    def get_all_movies_from_catalog() -> Response:
        """Retrieve all movies in the catalog.

        Returns:
            JSON response containing the list of movies.

        Raises:
            500 error if there is an issue retrieving the catalog.

        """
        try:
            app.logger.info("Received request to retrieve all movies from the catalog.")

            movies = catalog_model.get_all_movies()

            app.logger.info(f"Successfully retrieved {len(movies)} movies from the catalog.")
            return make_response(jsonify({
                "status": "success",
                "movies": movies
            }), 200)

        except Exception as e:
            app.logger.error(f"Failed to retrieve movies from catalog: {e}")
            return make_response(jsonify({
                "status": "error",
                "message": "An internal error occurred while retrieving the catalog",
                "details": str(e)
            }), 500)


    @app.route('/api/get-movie-from-catalog-by-track-number/<int:track_number>', methods=['GET'])
    @login_required
    def get_movie_by_track_number(track_number: int) -> Response:
        """Retrieve a movie from the catalog by track number.

        Path Parameter:
            - track_number (int): The track number of the movie.

        Returns:
            JSON response containing movie details.

        Raises:
            404 error if the track number is not found.
            500 error if there is an issue retrieving the movie.

        """
        try:
            app.logger.info(f"Received request to retrieve movie at track number {track_number}.")

            movie = catalog_model.get_movie_by_track_number(track_number)

            app.logger.info(f"Successfully retrieved movie: {movie.title} (Track {track_number}).")
            return make_response(jsonify({
                "status": "success",
                "movie": movie
            }), 200)

        except ValueError as e:
            app.logger.warning(f"Track number {track_number} not found: {e}")
            return make_response(jsonify({
                "status": "error",
                "message": str(e)
            }), 404)

        except Exception as e:
            app.logger.error(f"Failed to retrieve movie by track number {track_number}: {e}")
            return make_response(jsonify({
                "status": "error",
                "message": "An internal error occurred while retrieving the movie",
                "details": str(e)
            }), 500)


    @app.route('/api/get-current-movie', methods=['GET'])
    @login_required
    def get_current_movie() -> Response:
        """Retrieve the current movie being played.

        Returns:
            JSON response containing current movie details.

        Raises:
            500 error if there is an issue retrieving the current movie.

        """
        try:
            app.logger.info("Received request to retrieve the current movie.")

            current_movie = catalog_model.get_current_movie()

            app.logger.info(f"Successfully retrieved current movie: {current_movie.title}.")
            return make_response(jsonify({
                "status": "success",
                "current_movie": current_movie
            }), 200)

        except Exception as e:
            app.logger.error(f"Failed to retrieve current movie: {e}")
            return make_response(jsonify({
                "status": "error",
                "message": "An internal error occurred while retrieving the current movie",
                "details": str(e)
            }), 500)


    @app.route('/api/get-catalog-length-duration', methods=['GET'])
    @login_required
    def get_catalog_length_and_duration() -> Response:
        """Retrieve the length (number of movies) and total duration of the catalog.

        Returns:
            JSON response containing the catalog length and total duration.

        Raises:
            500 error if there is an issue retrieving catalog information.

        """
        try:
            app.logger.info("Received request to retrieve catalog length and duration.")

            catalog_length = catalog_model.get_catalog_length()
            catalog_duration = catalog_model.get_catalog_duration()

            app.logger.info(f"Catalog contains {catalog_length} movies with a total duration of {catalog_duration} seconds.")
            return make_response(jsonify({
                "status": "success",
                "catalog_length": catalog_length,
                "catalog_duration": catalog_duration
            }), 200)

        except Exception as e:
            app.logger.error(f"Failed to retrieve catalog length and duration: {e}")
            return make_response(jsonify({
                "status": "error",
                "message": "An internal error occurred while retrieving catalog details",
                "details": str(e)
            }), 500)


    ############################################################
    #
    # Arrange Catalog
    #
    ############################################################


    @app.route('/api/move-movie-to-beginning', methods=['POST'])
    @login_required
    def move_movie_to_beginning() -> Response:
        """Move a movie to the beginning of the catalog.

        Expected JSON Input:
            - title (str): The title of the movie.
            - year (int): The year the movie was released.

        Returns:
            Response: JSON response indicating success or an error message.

        Raises:
            400 error if required fields are missing.
            500 error if an error occurs while updating the catalog.

        """
        try:
            data = request.get_json()

            required_fields = ["title", "year"]
            missing_fields = [field for field in required_fields if field not in data]

            if missing_fields:
                app.logger.warning(f"Missing required fields: {missing_fields}")
                return make_response(jsonify({
                    "status": "error",
                    "message": f"Missing required fields: {', '.join(missing_fields)}"
                }), 400)

            title, year = data["title"], data["year"]
            app.logger.info(f"Received request to move movie to beginning: {title} ({year})")

            movie = Movies.get_movie_by_compound_key(title, year)
            catalog_model.move_movie_to_beginning(movie.id)

            app.logger.info(f"Successfully moved movie to beginning: {title} ({year})")
            return make_response(jsonify({
                "status": "success",
                "message": f"Movie '{title}' moved to beginning"
            }), 200)

        except Exception as e:
            app.logger.error(f"Failed to move movie to beginning: {e}")
            return make_response(jsonify({
                "status": "error",
                "message": "An internal error occurred while moving the movie",
                "details": str(e)
            }), 500)


    @app.route('/api/move-movie-to-end', methods=['POST'])
    @login_required
    def move_movie_to_end() -> Response:
        """Move a movie to the end of the catalog.

        Expected JSON Input:
            - title (str): The title of the movie.
            - year (int): The year the movie was released.

        Returns:
            Response: JSON response indicating success or an error message.

        Raises:
            400 error if required fields are missing.
            500 if an error occurs while updating the catalog.

        """
        try:
            data = request.get_json()

            required_fields = ["title", "year"]
            missing_fields = [field for field in required_fields if field not in data]

            if missing_fields:
                app.logger.warning(f"Missing required fields: {missing_fields}")
                return make_response(jsonify({
                    "status": "error",
                    "message": f"Missing required fields: {', '.join(missing_fields)}"
                }), 400)

            title, year = data["title"], data["year"]
            app.logger.info(f"Received request to move movie to end: {title} ({year})")

            movie = Movies.get_movie_by_compound_key(title, year)
            catalog_model.move_movie_to_end(movie.id)

            app.logger.info(f"Successfully moved movie to end: {title} ({year})")
            return make_response(jsonify({
                "status": "success",
                "message": f"Movie '{title}' moved to end"
            }), 200)

        except Exception as e:
            app.logger.error(f"Failed to move movie to end: {e}")
            return make_response(jsonify({
                "status": "error",
                "message": "An internal error occurred while moving the movie",
                "details": str(e)
            }), 500)


    @app.route('/api/move-movie-to-track-number', methods=['POST'])
    @login_required
    def move_movie_to_track_number() -> Response:
        """Move a movie to a specific track number in the catalog.

        Expected JSON Input:
            - title (str): The title of the movie.
            - year (int): The year the movie was released.
            - track_number (int): The new track number to move the movie to.

        Returns:
            Response: JSON response indicating success or an error message.

        Raises:
            400 error if required fields are missing.
            500 error if an error occurs while updating the catalog.
        """
        try:
            data = request.get_json()

            required_fields = ["title", "year", "track_number"]
            missing_fields = [field for field in required_fields if field not in data]

            if missing_fields:
                app.logger.warning(f"Missing required fields: {missing_fields}")
                return make_response(jsonify({
                    "status": "error",
                    "message": f"Missing required fields: {', '.join(missing_fields)}"
                }), 400)

            title, year, track_number = data["title"], data["year"], data["track_number"]
            app.logger.info(f"Received request to move movie to track number {track_number}: {title} ({year})")

            movie = Movies.get_movie_by_compound_key(title, year)
            catalog_model.move_movie_to_track_number(movie.id, track_number)

            app.logger.info(f"Successfully moved movie to track {track_number}: {title} ({year})")
            return make_response(jsonify({
                "status": "success",
                "message": f"Movie '{title}' moved to track {track_number}"
            }), 200)

        except Exception as e:
            app.logger.error(f"Failed to move movie to track number: {e}")
            return make_response(jsonify({
                "status": "error",
                "message": "An internal error occurred while moving the movie",
                "details": str(e)
            }), 500)


    @app.route('/api/swap-movies-in-catalog', methods=['POST'])
    @login_required
    def swap_movies_in_catalog() -> Response:
        """Swap two movies in the catalog by their track numbers.

        Expected JSON Input:
            - track_number_1 (int): The track number of the first movie.
            - track_number_2 (int): The track number of the second movie.

        Returns:
            Response: JSON response indicating success or an error message.

        Raises:
            400 error if required fields are missing.
            500 error if an error occurs while swapping movies in the catalog.
        """
        try:
            data = request.get_json()

            required_fields = ["track_number_1", "track_number_2"]
            missing_fields = [field for field in required_fields if field not in data]

            if missing_fields:
                app.logger.warning(f"Missing required fields: {missing_fields}")
                return make_response(jsonify({
                    "status": "error",
                    "message": f"Missing required fields: {', '.join(missing_fields)}"
                }), 400)

            track_number_1, track_number_2 = data["track_number_1"], data["track_number_2"]
            app.logger.info(f"Received request to swap movies at track numbers {track_number_1} and {track_number_2}")

            movie_1 = catalog_model.get_movie_by_track_number(track_number_1)
            movie_2 = catalog_model.get_movie_by_track_number(track_number_2)
            catalog_model.swap_movies_in_catalog(movie_1.id, movie_2.id)

            app.logger.info(f"Successfully swapped movies: {movie_1.title} <-> {movie_2.title}")
            return make_response(jsonify({
                "status": "success",
                "message": f"Swapped movies: {movie_1.title} <-> {movie_2.title}"
            }), 200)

        except Exception as e:
            app.logger.error(f"Failed to swap movies in catalog: {e}")
            return make_response(jsonify({
                "status": "error",
                "message": "An internal error occurred while swapping movies",
                "details": str(e)
            }), 500)



    ############################################################
    #
    # Leaderboard / Stats
    #
    ############################################################


    @app.route('/api/movie-leaderboard', methods=['GET'])
    def get_movie_leaderboard() -> Response:
        """
        Route to retrieve a leaderboard of movies sorted by play count.

        Returns:
            JSON response with a sorted leaderboard of movies.

        Raises:
            500 error if there is an issue generating the leaderboard.

        """
        try:
            app.logger.info("Received request to generate movie leaderboard")

            leaderboard_data = Movies.get_all_movies(sort_by_play_count=True)

            app.logger.info(f"Successfully generated movie leaderboard with {len(leaderboard_data)} entries")
            return make_response(jsonify({
                "status": "success",
                "leaderboard": leaderboard_data
            }), 200)

        except Exception as e:
            app.logger.error(f"Failed to generate movie leaderboard: {e}")
            return make_response(jsonify({
                "status": "error",
                "message": "An internal error occurred while generating the leaderboard",
                "details": str(e)
            }), 500)
        
    app.register_blueprint(movie_bp, url_prefix="/api")

    return app

if __name__ == '__main__':
    app = create_app()
    app.logger.info("Starting Flask app...")
    try:
        app.run(debug=True, host='0.0.0.0', port=5000)
    except Exception as e:
        app.logger.error(f"Flask app encountered an error: {e}")
    finally:
        app.logger.info("Flask app has stopped.")
