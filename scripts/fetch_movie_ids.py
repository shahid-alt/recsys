import os
import time
import traceback
from typing import List

from tqdm import tqdm

from dotenv import load_dotenv
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from db.connect import SessionLocal
from models.tmdb import MovieID, Genre
from utils.db_helpers import save_batch
from concurrent.futures import ThreadPoolExecutor, as_completed

db_session = SessionLocal()
https_session = requests.Session()
retries = Retry(
    total=5,
    backoff_factor=1,
    allowed_methods={"HEAD", "GET", "OPTIONS"},
    status_forcelist=[429,502,503,504]
)
adapter = HTTPAdapter(max_retries=retries)
https_session.mount('https://', adapter=adapter)

load_dotenv()
bearer_token = os.getenv("BEARER_TOKEN")
if not bearer_token:
    raise ValueError("Missing BEARER_TOKEN in .env")

endpoint = "https://api.themoviedb.org/3/discover/movie?primary_release_year={}&with_genres={}&page={}"

header = {
    "accept": "application/json",
    "Authorization": f"Bearer {bearer_token}",
    "User-Agent": "tmdb-fetcher/1.0"
}

def fetch_page(year, genre, page) -> List[int]:
    """
    Fetches the Movie IDs from a particular year, all the genres and pages from TMDB

    Args:
        year (int): Year of the movie
        genre (string): TMDB Genre ID
        page (int): Page Number (Page starts from 1, max limit is 500)

    Returns:
        List[int]: List containing the movie IDs from a particular page, genre and year.
    
    Raises:
        SSLError: If any SSLError occurs.
        Exception: If any unexpected exception occurs (logged with traceback).

    Notes:
        - Handles rate limiting (status code 429) using exponential backoff.
        - Returns empty list if no movies are found (status code 404).

    """
    tries = 0
    max_tries = 3
    for tries in range(max_tries):
        try:
            url = endpoint.format(year, genre, page)
            response = https_session.get(url=url, headers=header, timeout=5)
            if response.status_code == 200:
                    movies = response.json().get('results', [])
                    if not movies:
                         return []
                    return [movie['id'] for movie in movies]
            if response.status_code == 429:
                    print(f'Rate limited on page: {page}, backing off...')
                    time.sleep((2**tries)+1)
                    continue
            if response.status_code == 404:
                print(f"Resource Not Found for Year: {year}, Genre: {genre}, and Page: {page}")
                return []
            else:
                print(f'TMDB Exception: {response.status_code} - {response.text}')
                return []
        except requests.exceptions.SSLError as sslerror:
            print(f'[SSLError]: {sslerror}')
            time.sleep((2**tries)+1)
        except Exception as e:
            print(f"[Exception]: {e}")
            traceback.print_exc()

def main():
    """
    Fetches and saves the movie IDs for all genres and years.

    Workflow:
        1. Retrieves all then genre IDs from the database.
        2. Fetches movie IDs for each genre, year and page in parallel using ThreadPoolExecutor.
        3. Batches and saves the IDs in database in chunks of BATCH_SIZE.

    Notes:
        - Skips existing movie IDs to avoid duplication.
        - Logs progress and errors using tqdm.
    """
    GENRES = {genre.id:genre.name for genre in db_session.query(Genre).all()}
    GENRE_IDS = list(GENRES.keys())
    START_YEAR = 2021
    END_YEAR = 2022
    TOTAL = (END_YEAR-START_YEAR)*len(GENRE_IDS)*500
    new_movies_count = 0
    try:
        BATCH_SIZE = 5000
        movies_ids = []
        existing_ids = {_id[0] for _id in db_session.query(MovieID.id).all()}

        with tqdm(total=TOTAL, desc=f"Fetching Movies from {START_YEAR} to {END_YEAR}") as pbar:
            for year in range(START_YEAR, END_YEAR):
                for genre in GENRE_IDS:
                    workers = 50
                    new_movies = []
                    with ThreadPoolExecutor(max_workers=workers) as executor:
                        futures = [executor.submit(fetch_page, year, genre, page) for page in range(1, 501)]
                        for future in as_completed(futures):
                            movies = future.result()
                            pbar.update(1)
                            if movies:
                                new_movies = [movie_id for movie_id in movies if movie_id not in existing_ids]
                                new_movies_count += len(new_movies)
                                existing_ids.update(new_movies)
                                movies_ids.extend(MovieID(id=movie_id) for movie_id in new_movies)
                            if len(movies_ids) >= BATCH_SIZE:
                                tqdm.write(f'Commiting a batch in Database')
                                save_batch(records=movies_ids, session=db_session)
                                movies_ids.clear() 
                    tqdm.write(f"Completed batch for {year}-{GENRES[genre]}")
            tqdm.write(f"Committing the data in Database")
            if movies_ids: 
                save_batch(records=movies_ids, session=db_session)
                movies_ids.clear()
            tqdm.write(f"Total {new_movies_count} New Movie IDs pushed to DB.")
    except Exception as e:
        print(f"Exception Occured: {e}")
        db_session.rollback()
    finally:
        db_session.close()

if __name__ == '__main__':
    main()