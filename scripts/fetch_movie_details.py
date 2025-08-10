import random
import os
import time
import traceback
from typing import List, Optional, Tuple

from tqdm import tqdm

from dotenv import load_dotenv
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from requests.exceptions import SSLError
from db.connect import SessionLocal
from models.tmdb import Movie, MovieID, MovieGenre
from utils.db_helpers import save_batch
from concurrent.futures import ThreadPoolExecutor, as_completed

db_session = SessionLocal()

load_dotenv()
bearer_token = os.getenv("BEARER_TOKEN")
if not bearer_token:
    raise ValueError("Missing BEARER_TOKEN in .env")

endpoint = "https://api.themoviedb.org/3/movie/{}"

header = {
    "accept": "application/json",
    "Authorization": f"Bearer {bearer_token}",
    "User-Agent": "tmdb-fetcher/1.0"
}


https_session = requests.Session()
retries = Retry(
    total=5,
    backoff_factor=1,
    allowed_methods=["HEAD","GET","OPTIONS"],
    status_forcelist=[429,502,503,504] 
)
adapter = HTTPAdapter(max_retries=retries)
https_session.mount('https://', adapter=adapter)

failed_ids = []

def fetch_data(movie_id: int) -> Optional[Tuple[List[MovieGenre], Movie]]:
    """
    Retrieves the movie details and associated genres using Unique ID of the movie.

    Args:
        movie_id: Unique ID of the Movie

    Returns:
        Optional[Tuple[List[MovieGenre]: A tuple containing:
            - List[MovieGenre]:  Genres to which the movie belongs.
            - Movie: Serialized Movie object containing fields:
                - id (int): Movie ID
                - is_adult (bool): Whether the movie is adult or not.
                - language (str):  Language of the movie.
                - original_title (str): Title in language of the movie.
                - overview (str): Plot summary.
                - poster_path (str): Path of the poster in TMDB.
                - release_date (str): Date of movie release.
                - runtime (int): Runtime of the movie.
                - title (str): Title of movie in english.
                - status (str): Status of movie (e.g. - Released, In-Production, etc.).
                - vote_average (float): Voting average of the movie in TMBD. 
    
    Raises:
         SSLError: If any SSLError occurs.
         Exception: If any unexpected error occurs (logged with traceback).
        
    Notes:
        - Handles Rate Limiting (status code 429) with exponential backoff.
        - Returns None if no movie is found (status code 404).
    """
    max_attempts = 3
    for tries in range(max_attempts):
        try:
            response = https_session.get(endpoint.format(movie_id), headers=header, timeout=5)
            if response.status_code == 200:
                data = response.json()
                genres = [MovieGenre(genre_id=genre['id'], movie_id=movie_id) for genre in data.get('genres',[])]
                return genres, Movie(
                        id=movie_id,
                        is_adult=data.get('adult', False),
                        language=data.get('original_language'),
                        original_title=data.get('original_title'),
                        overview=data.get('overview'),
                        poster_path=data.get('poster_path'),
                        release_date=data.get('release_date'),
                        runtime=data.get('runtime'),
                        title=data.get('title'),
                        status=data.get('status'),
                        vote_average=data.get('vote_average')
                ) 
            if response.status_code == 429:
                print(f'Rate Limit Exceeded - Movie ID: {movie_id}')
                time.sleep((2**tries)+1)
            if response.status_code == 404:
                print(f'Resource Not Found for Movie ID: {movie_id}')
            else:
                print(f'[Error] ID: {movie_id}, Status: {response.status_code}')
                failed_ids.append(movie_id)
        except SSLError as sslerror:
            print(f'SSLError for Movie ID: {movie_id}, {sslerror}')
            time.sleep((2**tries)+1)
        except Exception as exception:
            print(f'Exception: {exception}')
            traceback.print_exc()

def main():
    """
    Fetches and save the details of the movies in database.

    Workflow:
        1. Retrieves the movie IDs in the database.
        2. Fetches the genres and data of each movie in parallel using ThreadPoolExecutor.
        3. Batches and saves the data in database in chunks of BATCH_SIZE

    Notes:
        - Skips existing Movie IDs to avoid duplication.
        - Logs the progress and errors using tqdm.
    """
    try:
        movies = []
        genres = []
        max_workers = 60
        BATCH_SIZE = 1000
        movie_ids = [movie.id for movie in db_session.query(MovieID).all()]
        random.shuffle(movie_ids)
        existing_movie_ids = set(db_session.query(Movie.id).all())
        existing_movie_genres = set(db_session.query(MovieGenre.genre_id, MovieGenre.movie_id).all())
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            with tqdm(total=len(movie_ids), desc='Fetching Movie Details....') as pbar:
                futures = [executor.submit(fetch_data, id) for id in movie_ids]
                for future in as_completed(futures):
                    result = future.result()
                    if result is None:
                        continue

                    movie_genres, movie = result
                    if movie and movie.id not in existing_movie_ids:
                        existing_movie_ids.add(movie.id)
                        movies.append(movie)

                        new_genres = [
                                movie_genre for movie_genre in movie_genres 
                                if (movie_genre.genre_id, movie_genre.movie_id) not in existing_movie_genres
                            ]
                        
                        if new_genres:
                            genres.extend(new_genres)
                            existing_movie_genres.update((movie_genre.genre_id, movie_genre.movie_id) for movie_genre in new_genres)

                    if len(movies) >= BATCH_SIZE:
                        save_batch(records=movies, session=db_session)
                        movies.clear()
                    if len(genres) >= BATCH_SIZE:
                        save_batch(records=genres, session=db_session)
                        genres.clear()
                    pbar.update(1)
        if movies:
            save_batch(records=movies, session=db_session)
            movies.clear()
        if genres:
            save_batch(records=genres, session=db_session)
            genres.clear()
        print(f'Number of Movie Details uploaded: {len(existing_movie_ids)}')       
    except Exception as exception:
        print(f'[EXCEPTION]: {exception}')
        db_session.rollback()
    finally:
        db_session.close()
    if failed_ids:
        print(f'Failed IDs: {failed_ids}, retry them....')

if __name__ == '__main__':
    main()