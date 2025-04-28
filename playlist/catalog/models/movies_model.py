import logging

from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from catalog.db import db
from catalog.utils.logger import configure_logger
from catalog.utils.api_utils import get_random


logger = logging.getLogger(__name__)
configure_logger(logger)


class Movies(db.Model):
    """Represents a Movie in the catalog.

    This model maps to the 'movies' table and stores metadata such as
    title, genre, release year, and duration.

    Used in a Flask-SQLAlchemy application for catalog management,
    user interaction, and data-driven movie operations.
    """

    __tablename__ = "Movies"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    genre = db.Column(db.String, nullable=False)
    duration = db.Column(db.Integer, nullable=False)
    play_count = db.Column(db.Integer, nullable=False, default=0)

    def validate(self) -> None:
        """
            Validates the moivie instance before committing to the database.
            raises ValueError: If any required fields are invalid.
        """
        if not self.title or not isinstance(self.title, str):
            raise ValueError("Title must be a non-empty string.")
        if not isinstance(self.year, int) or self.year <= 1900:
            raise ValueError("Year must be an integer greater than 1900.")
        if not self.genre or not isinstance(self.genre, str):
            raise ValueError("Genre must be a non-empty string.")
        if not isinstance(self.duration, int) or self.duration <= 0:
            raise ValueError("Duration must be a positive integer.")

    @classmethod
    def create_movie(cls, title: str, year: int, genre: str, duration: int) -> None:
        """
            Creates a new movie in the movies table using SQLAlchemy.

            input:  title (str): The movie title.
                    year (int): The year the movie was released.
                    genre (str): The movies genre.
                    duration (int): The duration of the movie in minutes.
                    play_count (int): The play count of the movie in the catalog
            raises: ValueError: If any field is invalid or if a movie with the same compound key already exists.
            SQLAlchemyError: For any other database-related issues.
        """
        logger.info(f"Received request to create movie: {title} ({year})")

        try:
            movie = Movies(
                title=title.strip(),
                year=year,
                genre=genre.strip(),
                duration=duration
            )
            movie.validate()
        except ValueError as e:
            logger.warning(f"Validation failed: {e}")
            raise

        try:
            # Check for existing movie with same compound key (artist, title, year)
            existing = Movies.query.filter_by(title=title.strip(), year=year).first()
            if existing:
                logger.error(f"Movie already exists: {title} ({year})")
                raise ValueError(f"Movie with title '{title}' and year {year} already exists.")

            db.session.add(movie)
            db.session.commit()
            logger.info(f"Movie successfully added: {title} ({year})")

        except IntegrityError:
            logger.error(f"Movie already exists: {title} ({year})")
            db.session.rollback()
            raise ValueError(f"movie with title '{title}' and year {year} already exists.")

        except SQLAlchemyError as e:
            logger.error(f"Database error while creating movie: {e}")
            db.session.rollback()
            raise

    @classmethod
    def delete_movie(cls, movie_id: int) -> None:
        """
            Permanently deletes a movie from the catalog by ID.
    
            input: movie_id (int): The ID of the movie to delete.
            raises: ValueError: If the movie with the given ID does not exist.
            SQLAlchemyError: For any database-related issues.
            """
        logger.info(f"Received request to delete movie with ID {movie_id}")

        try:
            movie = cls.query.get(movie_id)
            if not movie:
                logger.warning(f"Attempted to delete non-existent movie with ID {movie_id}")
                raise ValueError(f"Movie with ID {movie_id} not found")

            db.session.delete(movie_id)
            db.session.commit()
            logger.info(f"Successfully deleted movie with ID {movie_id}")

        except SQLAlchemyError as e:
            logger.error(f"Database error while deleting movie with ID {movie_id}: {e}")
            db.session.rollback()
            raise

    @classmethod
    def get_movie_by_id(cls, movie_id: int) -> "Movies":
        """
        Retrieves a movie from the catalog by its ID.
        input: movie_id (int): The ID of the movie to retrieve.
        returns: Movies: The movie instance corresponding to the ID.
        raises: ValueError: If no movie with the given ID is found.
                SQLAlchemyError: If a database error occurs.
        """
        logger.info(f"Attempting to retrieve movie with ID {movie_id}")

        try:
            movie = cls.query.get(movie_id)

            if not movie:
                logger.info(f"Movie with ID {movie_id} not found")
                raise ValueError(f"Movie with ID {movie_id} not found")

            logger.info(f"Successfully retrieved movie: {movie.title} ({movie.year})")
            return movie

        except SQLAlchemyError as e:
            logger.error(f"Database error while retrieving movie by ID {movie_id}: {e}")
            raise

    @classmethod
    def get_movie_by_compound_key(cls, artist: str, title: str, year: int) -> "Movies":
        """
        Retrieves a movie from the catalog by its compound key (title, year).
        input:  title (str): The title of the movie.
                year (int): The year the movie was released.
        result: movies: The movie instance matching the provided compound key.
        ValueError: If no matching movie is found.
        SQLAlchemyError: If a database error occurs.
        """
        logger.info(f"Attempting to retrieve movie with title '{title}' and year {year}")

        try:
            movie = cls.query.filter_by(title=title.strip(), year=year).first()

            if not movie:
                logger.info(f"title '{title}' and year {year} not found")
                raise ValueError(f"title '{title}' and year {year} not found")

            logger.info(f"Successfully retrieved movie: {movie.title} ({movie.year})")
            return movie

        except SQLAlchemyError as e:
            logger.error(
                f"Database error while retrieving movie by compound key "
                f"title '{title}', year {year}): {e}"
            )
            raise

    @classmethod
    def get_all_movie(cls, sort_by_play_count: bool = False) -> list[dict]:
        """
        Retrieves all movies from the catalog as dictionaries.
            input: sort_by_play_count (bool): If True, sort the movies by play count in descending order.
            result: list[dict]: A list of dictionaries representing all movies with play_count.
            raises: SQLAlchemyError: If any database error occurs.
        """
        logger.info("Attempting to retrieve all movies from the catalog")

        try:
            query = cls.query
            if sort_by_play_count:
                query = query.order_by(cls.play_count.desc())

            movies = query.all()

            if not movies:
                logger.warning("The movie catalog is empty.")
                return []

            results = [
                {
                    "id": movie.id,
                    "title": movie.title,
                    "year": movie.year,
                    "genre": movie.genre,
                    "duration": movie.duration,
                    "play_count": movie.play_count,
                }
                for movie in movies
            ]

            logger.info(f"Retrieved {len(results)} movie from the catalog")
            return results

        except SQLAlchemyError as e:
            logger.error(f"Database error while retrieving all movies: {e}")
            raise

    @classmethod
    def get_random_movie(cls) -> dict:
        """
        Retrieves a random movie from the catalog as a dictionary.

        Returns:
            dict: A randomly selected movie dictionary.
        """
        all_movies = cls.get_all_movies()

        if not all_movies:
            logger.warning("Cannot retrieve random movie because the movie catalog is empty.")
            raise ValueError("The movie catalog is empty.")

        index = get_random(len(all_movies))
        logger.info(f"Random index selected: {index} (total movies: {len(all_movies)})")

        return all_movies[index - 1]

    def update_play_count(self) -> None:
        """
        Increments the play count of the current movie instance.

        Raises:
            ValueError: If the movie does not exist in the database.
            SQLAlchemyError: If any database error occurs.
        """

        logger.info(f"Attempting to update play count for movie with ID {self.id}")

        try:
            movie = Movies.query.get(self.id)
            if not movie:
                logger.warning(f"Cannot update play count: Movie with ID {self.id} not found.")
                raise ValueError(f"Movie with ID {self.id} not found")

            movie.play_count += 1
            db.session.commit()

            logger.info(f"Play count incremented for movie with ID: {self.id}")

        except SQLAlchemyError as e:
            logger.error(f"Database error while updating play count for movie with ID {self.id}: {e}")
            db.session.rollback()
            raise
