from concurrent.futures import ThreadPoolExecutor, as_completed
import os
import time
import traceback
from typing import List

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from tqdm import tqdm

from dotenv import load_dotenv
from models.tmdb import Credit, MovieID
from db.connect import Base, engine, SessionLocal
from utils.db import save_batch

Base.metadata.create_all(bind=engine)
db_session = SessionLocal()
https_session = requests.Session()
retries = Retry(
    total=5,
    backoff_factor=1,
    status_forcelist=[429, 502, 503, 504],
    allowed_methods=["HEAD", "GET", "OPTIONS"]
)
adapter = HTTPAdapter(max_retries=retries)
https_session.mount('https://', adapter=adapter)

load_dotenv()
bearer_token = os.getenv('BEARER_TOKEN')
if not bearer_token:
    raise ValueError("Missing BEARER_TOKEN in .env")

endpoint = "https://api.themoviedb.org/3/movie/{}/credits"

header = {
    'accept': 'application/json',
    'Authorization': f'Bearer {bearer_token}',
    "User-Agent": "tmdb-fetcher/1.0"
}

def fetch_movie_credit(movie_id: int) -> List[Credit]:
    max_attempts = 3
    for tries in range(max_attempts):
        cast_credits = []
        try:
            response = https_session.get(endpoint.format(movie_id), headers=header, timeout=5)
            if response.status_code == 200:
                data = response.json()
                casts = data.get('cast', [])
                for cast in casts:
                    gender = cast.get('gender')
                    person_id = cast.get('id')
                    name = cast.get('name')
                    character_name = cast.get('character')
                    credit_id = cast.get('credit_id')
                    cast_credits.append(
                        Credit(
                            id=credit_id,
                            movie_id=movie_id,
                            gender=gender,
                            person_id=person_id,
                            name=name,
                            character_name=character_name
                        )
                    )
                if len(cast_credits) == len(casts):
                    return cast_credits
                else:
                    print(f'Lengths of cast_credits & casts are not equal. Lenghts - {len(cast_credits)}, {len(casts)}')
            if response.status_code == 429:
                print(f'Rate Limited for Movie ID: {movie_id}...')
                time.sleep(2**tries+1)
            if response.status_code == 404:
                print(f'Resource not found for Movie ID - {movie_id}')
                return []      
            else:
                print(f'TMDB Exception for [Movie ID:{movie_id}] - {response.status_code} - {response.text}')
        except requests.exceptions.SSLError as sslerror:
            print(f'SSLError: {sslerror}')
            time.sleep(2)
        except Exception as e:
            print(f'[Exception]: {e}')
            traceback.print_exc()

def main() -> None:  
    try:
        movie_ids = [movie.id for movie in db_session.query(MovieID).all()]
        existing_ids = {credit_id[0] for credit_id in db_session.query(Credit.id).all()}
        with tqdm(movie_ids, desc='Fetching Movie Credits...') as pbar:
            max_workers = 60
            BATCH_SIZE = 1000
            batch = []
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = [executor.submit(fetch_movie_credit, movie_id) for movie_id in movie_ids]
                for future in as_completed(futures):
                    credit_list = future.result()
                    pbar.update(1)
                    if credit_list:
                        new_credits = [credit for credit in credit_list if credit.id not in existing_ids]
                        existing_ids.update(credit.id for credit in new_credits)
                        batch.extend(new_credits)
                    if len(batch) >= BATCH_SIZE:
                        save_batch(records=batch, session=db_session)
                        batch.clear() 
        if batch:   
            save_batch(records=batch, session=db_session)
        print(f'Total Credits Inserted {len(existing_ids)}')
    except Exception as e:
        print(f'[Exception] - {e}')
        db_session.rollback()
    finally:
        db_session.close()

if __name__ == "__main__":
    main()