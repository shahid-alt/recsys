import os
import time
import traceback

from tqdm import tqdm

from dotenv import load_dotenv
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from db.connect import Base, engine, SessionLocal
from models.tmdb import MovieID, Genre
from utils.db import save_batch
from concurrent.futures import ThreadPoolExecutor, as_completed

Base.metadata.create_all(bind=engine)
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

def fetch_page(year, genre, page):
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
    GENRES = {genre.id:genre.name for genre in db_session.query(Genre).all()}
    GENRE_IDS = list(GENRES.keys())
    START_YEAR = 2025
    END_YEAR = 2026
    TOTAL = (END_YEAR-START_YEAR)*len(GENRE_IDS)*500
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
                                existing_ids.update(new_movies)
                                movies_ids.extend(MovieID(id=movie_id) for movie_id in new_movies)
                            if len(movies_ids) >= BATCH_SIZE:
                                tqdm.write(f'Commiting a batch in Database - Year:{year} - Genre: {GENRES[genre]}')
                                save_batch(records=movies_ids, session=db_session)
                                movies_ids.clear() 
                    tqdm.write(f"Completed batch for {year}-{GENRES[genre]}")
            tqdm.write(f"Committing the data in Database")
            if movies_ids: 
                save_batch(records=movies_ids, session=db_session)
                movies_ids.clear()
            tqdm.write(f"Total {len(existing_ids)} Movie IDs pushed to DB.")
    except Exception as e:
        print(f"Exception Occured: {e}")
        db_session.rollback()
    finally:
        db_session.close()

if __name__ == '__main__':
    main()