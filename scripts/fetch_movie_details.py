import random
import sys
import os
import time

from sqlalchemy import func
from tqdm import tqdm
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from requests.exceptions import SSLError
from db.connect import Base, engine, SessionLocal
from models.tmdb import Movie, MovieID
from concurrent.futures import ThreadPoolExecutor, as_completed

Base.metadata.create_all(bind=engine)
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

def fetch_data(movie_id):
    max_attempts = 3
    for tries in range(max_attempts):
        try:
            response = https_session.get(endpoint.format(movie_id), headers=header, timeout=5)
            if response.status_code == 200:
                data = response.json()
                return Movie(
                        id=movie_id,
                        is_adult=data.get('adult', False),
                        genres=str([genre['name'] for genre in data.get('genres',[])]),
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
            time.sleep(0.5)

def main():
    try:
        movies = []
        max_workers = 50
        BATCH_SIZE = 1000
        movie_ids = [movie.id for movie in db_session.query(MovieID).all()]
        random.shuffle(movie_ids)
        existing_movie_ids = {movie.id for movie in db_session.query(Movie).all()}
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            with tqdm(total=len(movie_ids), desc='Fetching Movie Details....') as pbar:
                futures = [executor.submit(fetch_data, id) for id in movie_ids]
                for future in as_completed(futures):
                    movie = future.result()
                    if movie and movie.id not in existing_movie_ids:
                        existing_movie_ids.add(movie.id)
                        movies.append(movie)
                    if len(movies) >= BATCH_SIZE:
                        db_session.bulk_save_objects(movies)
                        db_session.commit()
                        movies.clear()
                    pbar.update(1)
        if movies:
            db_session.bulk_save_objects(movies)
            db_session.commit()
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