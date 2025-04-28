import logging
import os
import time
from typing import List

from catalog.models.movies_model import Movies
from catalog.utils.api_utils import get_random
from catalog.utils.logger import configure_logger

logger = logging.getLogger(__name__)
configure_logger(logger)


class CatalogModel:
    """
    A class to manage a catalog of movies.

    """

    def __init__(self):
        """Initializes the CatalogModel with an empty catalog and the current track set to 1.

        The catalog is a list of movies, and the current track number is 1-indexed.
        The TTL (Time To Live) for movie caching is set to a default value from the environment variable "TTL",
        which defaults to 60 seconds if not set.

        """
        self.current_movie_number = 1
        self.catalog: List[int] = []
        self._movie_cache: dict[int, Movies] = {}
        self._ttl: dict[int, float] = {}
        self.ttl_seconds = int(os.getenv("TTL", 60))  # Default TTL is 60 seconds


    ##################################################
    # Movie Management Functions
    ##################################################

    def _get_movie_from_cache_or_db(self, movie_id: int) -> Movies:
        """
        Retrieves a movie by ID, using the internal cache if possible.

        This method checks whether a cached version of the movie is available
        and still valid. If not, it queries the database, updates the cache, and returns the movie.

        Args:
            movie_id (int): The unique ID of the movie to retrieve.

        Returns:
            Movies: The movie object corresponding to the given ID.

        Raises:
            ValueError: If the movie cannot be found in the database.
        """
        now = time.time()

        if movie_id in self._movie_cache and self._ttl.get(movie_id, 0) > now:
            logger.debug(f"Movie ID {movie_id} retrieved from cache")
            return self._movie_cache[movie_id]

        try:
            movie = Movies.get_movie_by_id(movie_id)
            logger.info(f"Movie ID {movie_id} loaded from DB")
        except ValueError as e:
            logger.error(f"Movie ID {movie_id} not found in DB: {e}")
            raise ValueError(f"Movie ID {movie_id} not found in database") from e

        self._movie_cache[movie_id] = movie
        self._ttl[movie_id] = now + self.ttl_seconds
        return movie

    def add_movie_to_catalog(self, movie_id: int) -> None:
        """
        Adds a movie to the catalog by ID, using the cache or database lookup.

        Args:
            movie_id (int): The ID of the movie to add to the catalog.

        Raises:
            ValueError: If the movie ID is invalid or already exists in the catalog.
        """
        logger.info(f"Received request to add movie with ID {movie_id} to the catalog")

        movie_id = self.validate_movie_id(movie_id, check_in_catalog=False)

        if movie_id in self.catalog:
            logger.error(f"Movie with ID {movie_id} already exists in the catalog")
            raise ValueError(f"Movie with ID {movie_id} already exists in the catalog")

        try:
            movie = self._get_movie_from_cache_or_db(movie_id)
        except ValueError as e:
            logger.error(f"Failed to add movie: {e}")
            raise

        self.catalog.append(movie.id)
        logger.info(f"Successfully added to catalog: {movie.artist} - {movie.title} ({movie.year})")


    def remove_movie_by_movie_id(self, movie_id: int) -> None:
        """Removes a movie from the catalog by its movie ID.

        Args:
            movie_id (int): The ID of the movie to remove from the catalog.

        Raises:
            ValueError: If the catalog is empty or the movie ID is invalid.

        """
        logger.info(f"Received request to remove movie with ID {movie_id}")

        self.check_if_empty()
        movie_id = self.validate_movie_id(movie_id)

        if movie_id not in self.catalog:
            logger.warning(f"Movie with ID {movie_id} not found in the catalog")
            raise ValueError(f"Movie with ID {movie_id} not found in the catalog")

        self.catalog.remove(movie_id)
        logger.info(f"Successfully removed movie with ID {movie_id} from the catalog")

    def remove_movie_by_track_number(self, track_number: int) -> None:
        """Removes a movie from the catalog by its track number (1-indexed).

        Args:
            track_number (int): The track number of the movie to remove.

        Raises:
            ValueError: If the catalog is empty or the track number is invalid.

        """
        logger.info(f"Received request to remove movie at track number {track_number}")

        self.check_if_empty()
        track_number = self.validate_track_number(track_number)
        catalog_index = track_number - 1

        logger.info(f"Successfully removed movie at track number {track_number}")
        del self.catalog[catalog_index]

    def clear_catalog(self) -> None:
        """Clears all movies from the catalog.

        Clears all movies from the catalog. If the catalog is already empty, logs a warning.

        """
        logger.info("Received request to clear the catalog")

        try:
            if self.check_if_empty():
                pass
        except ValueError:
            logger.warning("Clearing an empty catalog")

        self.catalog.clear()
        logger.info("Successfully cleared the catalog")


    ##################################################
    # Catalog Retrieval Functions
    ##################################################


    def get_all_movies(self) -> List[Movies]:
        """Returns a list of all movies in the catalog using cached movie data.

        Returns:
            List[Movie]: A list of all movies in the catalog.

        Raises:
            ValueError: If the catalog is empty.
        """
        self.check_if_empty()
        logger.info("Retrieving all movies in the catalog")
        return [self._get_movie_from_cache_or_db(movie_id) for movie_id in self.catalog]

    def get_movie_by_movie_id(self, movie_id: int) -> Movies:
        """Retrieves a movie from the catalog by its movie ID using the cache or DB.

        Args:
            movie_id (int): The ID of the movie to retrieve.

        Returns:
            Movie: The movie with the specified ID.

        Raises:
            ValueError: If the catalog is empty or the movie is not found.
        """
        self.check_if_empty()
        movie_id = self.validate_movie_id(movie_id)
        logger.info(f"Retrieving movie with ID {movie_id} from the catalog")
        movie = self._get_movie_from_cache_or_db(movie_id)
        logger.info(f"Successfully retrieved movie: {movie.artist} - {movie.title} ({movie.year})")
        return movie

    def get_movie_by_track_number(self, track_number: int) -> Movies:
        """Retrieves a movie from the catalog by its track number (1-indexed).

        Args:
            track_number (int): The track number of the movie to retrieve.

        Returns:
            Movie: The movie at the specified track number.

        Raises:
            ValueError: If the catalog is empty or the track number is invalid.
        """
        self.check_if_empty()
        track_number = self.validate_track_number(track_number)
        catalog_index = track_number - 1

        logger.info(f"Retrieving movie at track number {track_number} from catalog")
        movie_id = self.catalog[catalog_index]
        movie = self._get_movie_from_cache_or_db(movie_id)
        logger.info(f"Successfully retrieved movie: {movie.artist} - {movie.title} ({movie.year})")
        return movie

    def get_current_movie(self) -> Movies:
        """Returns the current movie being played.

        Returns:
            Movie: The currently playing movie.

        Raises:
            ValueError: If the catalog is empty.
        """
        self.check_if_empty()
        logger.info("Retrieving the current movie being played")
        return self.get_movie_by_track_number(self.current_track_number)

    def get_catalog_length(self) -> int:
        """Returns the number of movies in the catalog.

        Returns:
            int: The total number of movies in the catalog.

        """
        length = len(self.catalog)
        logger.info(f"Retrieving catalog length: {length} movies")
        return length

    def get_catalog_duration(self) -> int:
        """
        Returns the total duration of the catalog in seconds using cached movies.

        Returns:
            int: The total duration of all movies in the catalog in seconds.
        """
        total_duration = sum(self._get_movie_from_cache_or_db(movie_id).duration for movie_id in self.catalog)
        logger.info(f"Retrieving total catalog duration: {total_duration} seconds")
        return total_duration


    ##################################################
    # Catalog Movement Functions
    ##################################################


    def go_to_track_number(self, track_number: int) -> None:
        """Sets the current track number to the specified track number.

        Args:
            track_number (int): The track number to set as the current track.

        Raises:
            ValueError: If the catalog is empty or the track number is invalid.

        """
        self.check_if_empty()
        track_number = self.validate_track_number(track_number)
        logger.info(f"Setting current track number to {track_number}")
        self.current_track_number = track_number

    def go_to_random_track(self) -> None:
        """Sets the current track number to a randomly selected track.

        Raises:
            ValueError: If the catalog is empty.

        """
        self.check_if_empty()

        # Get a random index using the random.org API
        random_track = get_random(self.get_catalog_length())

        logger.info(f"Setting current track number to random track: {random_track}")
        self.current_track_number = random_track

    def move_movie_to_beginning(self, movie_id: int) -> None:
        """Moves a movie to the beginning of the catalog.

        Args:
            movie_id (int): The ID of the movie to move.

        Raises:
            ValueError: If the catalog is empty or the movie ID is invalid.

        """
        logger.info(f"Moving movie with ID {movie_id} to the beginning of the catalog")
        self.check_if_empty()
        movie_id = self.validate_movie_id(movie_id)

        self.catalog.remove(movie_id)
        self.catalog.insert(0, movie_id)

        logger.info(f"Successfully moved movie with ID {movie_id} to the beginning")

    def move_movie_to_end(self, movie_id: int) -> None:
        """Moves a movie to the end of the catalog.

        Args:
            movie_id (int): The ID of the movie to move.

        Raises:
            ValueError: If the catalog is empty or the movie ID is invalid.

        """
        logger.info(f"Moving movie with ID {movie_id} to the end of the catalog")
        self.check_if_empty()
        movie_id = self.validate_movie_id(movie_id)

        self.catalog.remove(movie_id)
        self.catalog.append(movie_id)

        logger.info(f"Successfully moved movie with ID {movie_id} to the end")

    def move_movie_to_track_number(self, movie_id: int, track_number: int) -> None:
        """Moves a movie to a specific track number in the catalog.

        Args:
            movie_id (int): The ID of the movie to move.
            track_number (int): The track number to move the movie to (1-indexed).

        Raises:
            ValueError: If the catalog is empty, the movie ID is invalid, or the track number is out of range.

        """
        logger.info(f"Moving movie with ID {movie_id} to track number {track_number}")
        self.check_if_empty()
        movie_id = self.validate_movie_id(movie_id)
        track_number = self.validate_track_number(track_number)

        catalog_index = track_number - 1

        self.catalog.remove(movie_id)
        self.catalog.insert(catalog_index, movie_id)

        logger.info(f"Successfully moved movie with ID {movie_id} to track number {track_number}")

    def swap_movies_in_catalog(self, movie1_id: int, movie2_id: int) -> None:
        """Swaps the positions of two movies in the catalog.

        Args:
            movie1_id (int): The ID of the first movie to swap.
            movie2_id (int): The ID of the second movie to swap.

        Raises:
            ValueError: If the catalog is empty, either movie ID is invalid, or attempting to swap the same movie.

        """
        logger.info(f"Swapping movies with IDs {movie1_id} and {movie2_id}")
        self.check_if_empty()
        movie1_id = self.validate_movie_id(movie1_id)
        movie2_id = self.validate_movie_id(movie2_id)

        if movie1_id == movie2_id:
            logger.error(f"Cannot swap a movie with itself: {movie1_id}")
            raise ValueError(f"Cannot swap a movie with itself: {movie1_id}")

        index1, index2 = self.catalog.index(movie1_id), self.catalog.index(movie2_id)

        self.catalog[index1], self.catalog[index2] = self.catalog[index2], self.catalog[index1]

        logger.info(f"Successfully swapped movies with IDs {movie1_id} and {movie2_id}")


    ##################################################
    # Catalog Playback Functions
    ##################################################


    def play_current_movie(self) -> None:
        """Plays the current movie and advances the catalog.

        Raises:
            ValueError: If the catalog is empty.

        """
        self.check_if_empty()
        current_movie = self.get_movie_by_track_number(self.current_track_number)

        logger.info(f"Playing movie: {current_movie.title} (ID: {current_movie.id}) at track number: {self.current_track_number}")
        current_movie.update_play_count()
        logger.info(f"Updated play count for movie: {current_movie.title} (ID: {current_movie.id})")

        self.current_track_number = (self.current_track_number % self.get_catalog_length()) + 1
        logger.info(f"Advanced to track number: {self.current_track_number}")

    def play_entire_catalog(self) -> None:
        """Plays all movies in the catalog from the beginning.

        Raises:
            ValueError: If the catalog is empty.

        """
        self.check_if_empty()
        logger.info("Starting to play the entire catalog.")

        self.current_track_number = 1
        for _ in range(self.get_catalog_length()):
            self.play_current_movie()

        logger.info("Finished playing the entire catalog.")

    def play_rest_of_catalog(self) -> None:
        """Plays the remaining movies in the catalog from the current track onward.

        Raises:
            ValueError: If the catalog is empty.

        """
        self.check_if_empty()
        logger.info(f"Playing the rest of the catalog from track number: {self.current_track_number}")

        for _ in range(self.get_catalog_length() - self.current_track_number + 1):
            self.play_current_movie()

        logger.info("Finished playing the rest of the catalog.")

    def rewind_catalog(self) -> None:
        """Resets the catalog to the first track.

        Raises:
            ValueError: If the catalog is empty.

        """
        self.check_if_empty()
        self.current_track_number = 1
        logger.info("Rewound catalog to the first track.")


    ##################################################
    # Utility Functions
    ##################################################


    ####################################################################################################
    #
    # Note: I am only testing these things once. EG I am not testing that everything rejects an empty
    # list as they all do so by calling this helper
    #
    ####################################################################################################

    def validate_movie_id(self, movie_id: int, check_in_catalog: bool = True) -> int:
        """
        Validates the given movie ID.

        Args:
            movie_id (int): The movie ID to validate.
            check_in_catalog (bool, optional): If True, verifies the ID is present in the catalog.
                                                If False, skips that check. Defaults to True.

        Returns:
            int: The validated movie ID.

        Raises:
            ValueError: If the movie ID is not a non-negative integer,
                        not found in the catalog (if check_in_catalog=True),
                        or not found in the database.
        """
        try:
            movie_id = int(movie_id)
            if movie_id < 0:
                raise ValueError
        except ValueError:
            logger.error(f"Invalid movie id: {movie_id}")
            raise ValueError(f"Invalid movie id: {movie_id}")

        if check_in_catalog and movie_id not in self.catalog:
            logger.error(f"Movie with id {movie_id} not found in catalog")
            raise ValueError(f"Movie with id {movie_id} not found in catalog")

        try:
            self._get_movie_from_cache_or_db(movie_id)
        except Exception as e:
            logger.error(f"Movie with id {movie_id} not found in database: {e}")
            raise ValueError(f"Movie with id {movie_id} not found in database")

        return movie_id

    def validate_track_number(self, track_number: int) -> int:
        """
        Validates the given track number, ensuring it is within the catalog's range.

        Args:
            track_number (int): The track number to validate.

        Returns:
            int: The validated track number.

        Raises:
            ValueError: If the track number is not a valid positive integer or is out of range.

        """
        try:
            track_number = int(track_number)
            if not (1 <= track_number <= self.get_catalog_length()):
                raise ValueError(f"Invalid track number: {track_number}")
        except ValueError as e:
            logger.error(f"Invalid track number: {track_number}")
            raise ValueError(f"Invalid track number: {track_number}") from e

        return track_number

    def check_if_empty(self) -> None:
        """
        Checks if the catalog is empty and raises a ValueError if it is.

        Raises:
            ValueError: If the catalog is empty.

        """
        if not self.catalog:
            logger.error("Catalog is empty")
            raise ValueError("Catalog is empty")
