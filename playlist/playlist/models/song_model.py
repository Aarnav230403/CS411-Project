import logging

from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from playlist.db import db
from playlist.utils.logger import configure_logger
from playlist.utils.api_utils import get_random


logger = logging.getLogger(__name__)
configure_logger(logger)


class Movies(db.Model):
    """Represents a Movie in the catalog.

    This model maps to the 'movies' table and stores metadata such as
    title, genre, release year, and duration.

    Used in a Flask-SQLAlchemy application for playlist management,
    user interaction, and data-driven song operations.
    """

    __tablename__ = "Movies"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    genre = db.Column(db.String, nullable=False)
    duration = db.Column(db.Integer, nullable=False)

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
    def create_song(cls, title: str, year: int, genre: str, duration: int) -> None:
        """
            Creates a new movie in the songs table using SQLAlchemy.

            input:  title (str): The movie title.
                    year (int): The year the movie was released.
                    genre (str): The movies genre.
                    duration (int): The duration of the movie in minutes.
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
            # Check for existing song with same compound key (artist, title, year)
            existing = Movies.query.filter_by(title=title.strip(), year=year).first()
            if existing:
                logger.error(f"Movie already exists: {title} ({year})")
                raise ValueError(f"Movie with title '{title}' and year {year} already exists.")

            db.session.add(movie)
            db.session.commit()
            logger.info(f"Movie successfully added: {artist} - {title} ({year})")

        except IntegrityError:
            logger.error(f"Movie already exists: title} ({year})")
            db.session.rollback()
            raise ValueError(f"Song with title '{title}' and year {year} already exists.")

        except SQLAlchemyError as e:
            logger.error(f"Database error while creating movie: {e}")
            db.session.rollback()
            raise

    @classmethod
    def delete_song(cls, movie_id: int) -> None:
        """
            Permanently deletes a movie from the catalog by ID.
    
            input: movie_id (int): The ID of the movie to delete.
            raises: ValueError: If the movie with the given ID does not exist.
            SQLAlchemyError: For any database-related issues.
            """
            logger.info(f"Received request to delete song with ID {movie_id}")

        try:
            movie = cls.query.get(movie_id)
            if not movie:
                logger.warning(f"Attempted to delete non-existent movie with ID {movie_id}")
                raise ValueError(f"Movie with ID {movie_id} not found")

            db.session.delete(movie_id)
            db.session.commit()
            logger.info(f"Successfully deleted song with ID {movie_id}")

        except SQLAlchemyError as e:
            logger.error(f"Database error while deleting movie with ID {movie_id}: {e}")
            db.session.rollback()
            raise

    @classmethod
    def get_song_by_id(cls, movie_id: int) -> "Movies":
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
                logger.info(f"Song with ID {movie_id} not found")
                raise ValueError(f"Song with ID {movie_id} not found")

            logger.info(f"Successfully retrieved song: {song.artist} - {song.title} ({song.year})")
            return song

        except SQLAlchemyError as e:
            logger.error(f"Database error while retrieving song by ID {song_id}: {e}")
            raise

    @classmethod
    def get_song_by_compound_key(cls, artist: str, title: str, year: int) -> "Songs":
        """
        Retrieves a song from the catalog by its compound key (artist, title, year).

        Args:
            artist (str): The artist of the song.
            title (str): The title of the song.
            year (int): The year the song was released.

        Returns:
            Songs: The song instance matching the provided compound key.

        Raises:
            ValueError: If no matching song is found.
            SQLAlchemyError: If a database error occurs.
        """
        logger.info(f"Attempting to retrieve song with artist '{artist}', title '{title}', and year {year}")

        try:
            song = cls.query.filter_by(artist=artist.strip(), title=title.strip(), year=year).first()

            if not song:
                logger.info(f"Song with artist '{artist}', title '{title}', and year {year} not found")
                raise ValueError(f"Song with artist '{artist}', title '{title}', and year {year} not found")

            logger.info(f"Successfully retrieved song: {song.artist} - {song.title} ({song.year})")
            return song

        except SQLAlchemyError as e:
            logger.error(
                f"Database error while retrieving song by compound key "
                f"(artist '{artist}', title '{title}', year {year}): {e}"
            )
            raise

    @classmethod
    def get_all_songs(cls, sort_by_play_count: bool = False) -> list[dict]:
        """
        Retrieves all songs from the catalog as dictionaries.

        Args:
            sort_by_play_count (bool): If True, sort the songs by play count in descending order.

        Returns:
            list[dict]: A list of dictionaries representing all songs with play_count.

        Raises:
            SQLAlchemyError: If any database error occurs.
        """
        logger.info("Attempting to retrieve all songs from the catalog")

        try:
            query = cls.query
            if sort_by_play_count:
                query = query.order_by(cls.play_count.desc())

            songs = query.all()

            if not songs:
                logger.warning("The song catalog is empty.")
                return []

            results = [
                {
                    "id": song.id,
                    "artist": song.artist,
                    "title": song.title,
                    "year": song.year,
                    "genre": song.genre,
                    "duration": song.duration,
                    "play_count": song.play_count,
                }
                for song in songs
            ]

            logger.info(f"Retrieved {len(results)} songs from the catalog")
            return results

        except SQLAlchemyError as e:
            logger.error(f"Database error while retrieving all songs: {e}")
            raise

    @classmethod
    def get_random_song(cls) -> dict:
        """
        Retrieves a random song from the catalog as a dictionary.

        Returns:
            dict: A randomly selected song dictionary.
        """
        all_songs = cls.get_all_songs()

        if not all_songs:
            logger.warning("Cannot retrieve random song because the song catalog is empty.")
            raise ValueError("The song catalog is empty.")

        index = get_random(len(all_songs))
        logger.info(f"Random index selected: {index} (total songs: {len(all_songs)})")

        return all_songs[index - 1]

    def update_play_count(self) -> None:
        """
        Increments the play count of the current song instance.

        Raises:
            ValueError: If the song does not exist in the database.
            SQLAlchemyError: If any database error occurs.
        """

        logger.info(f"Attempting to update play count for song with ID {self.id}")

        try:
            song = Songs.query.get(self.id)
            if not song:
                logger.warning(f"Cannot update play count: Song with ID {self.id} not found.")
                raise ValueError(f"Song with ID {self.id} not found")

            song.play_count += 1
            db.session.commit()

            logger.info(f"Play count incremented for song with ID: {self.id}")

        except SQLAlchemyError as e:
            logger.error(f"Database error while updating play count for song with ID {self.id}: {e}")
            db.session.rollback()
            raise
