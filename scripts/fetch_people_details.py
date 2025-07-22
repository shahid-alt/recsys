from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import os
import sys
from threading import Lock
import time

import sqlalchemy
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
import requests
from requests.adapters import HTTPAdapter
from requests.exceptions import SSLError
from urllib3.util.retry import Retry
from models.tmdb import Credit, People
from db.connect import Base, engine, SessionLocal

from tqdm import tqdm


load_dotenv()
bearer_token = os.getenv('BEARER_TOKEN')
if not bearer_token:
    raise ValueError("BEARER_TOKEN not found in .env file")

header = {
    'accept': 'Application/json',
    'Authorization': f"Bearer {bearer_token}",
    "User-Agent": "tmdb-fetcher/1.0"
}

https_session = requests.Session()
retries = Retry(
    total=5,
    backoff_factor=1,
    allowed_methods={"HEAD","GET","OPTIONS"},
    status_forcelist=[429,502,503,504]
)

adapter = HTTPAdapter(max_retries=retries)
https_session.mount('https://', adapter=adapter)

Base.metadata.create_all(bind=engine)

failed_ids = []
lock = Lock()

def get_gender(gender:int) -> str:
    gender_map = {
        0:'Not Specified',
        1:'Female',
        2:'Male',
        3:'Non-Binary'
    }
    return gender_map.get(gender, 'Not Specified')

def fetch_people_data(people_id: int) -> People:
    max_tries = 3
    for tries in range(max_tries):
        try:
            endpoint = "https://api.themoviedb.org/3/person/{}"
            response = https_session.get(url=endpoint.format(people_id), timeout=5, headers=header)
            if response.status_code == 200:
                data = response.json()
                return People(
                    id=people_id,
                    is_adult=data.get('adult'),
                    alias=json.dumps(data.get('also_known_as', []), ensure_ascii=False),
                    biography=data.get('biography'),
                    birthday=data.get('birthday'),
                    gender=get_gender(data.get('gender', 0)),
                    name=data.get('name'),
                    place_of_birth=data.get('place_of_birth'),
                    profile_path=data.get('profile_path')
                )
            if response.status_code == 404:
                print(f'Resource not found for People ID: {people_id}')
                return None
            if response.status_code == 429:
                print(f'Rate Limited for People ID: {people_id}')
                time.sleep((2**tries)+1)
            else:
                print(f'Error at People ID: {people_id} - {response.text} - {response.status_code}')
                with lock:
                    failed_ids.append(people_id)
                time.sleep(1)
        except SSLError as sslerror:
            print(f'SSLError at People ID: {people_id}  - {sslerror}')
            time.sleep((2**tries)+1)
        except Exception as e:
            print(f'[Exception]: {e}')
    return None

def save_batch(peoples_list):
    retries = 5
    for attempt in range(retries):
        session = SessionLocal()
        try:
            session.bulk_save_objects(peoples_list)
            session.commit()
            session.close()
            return
        except sqlalchemy.exc.OperationalError as e:
            if 'database is locked' in str(e):
                print(f"DB is locked, retrying commit {attempt + 1}/{retries}...")
                time.sleep(1 + attempt)
            else:
                session.rollback()
                session.close()
                raise
        finally:
            session.close()
    print("Failed to commit batch after retries.")

def main() -> None:
    db_session = SessionLocal()
    try:
        max_workers = 100
        people_ids = [id[0] for id in db_session.query(Credit.person_id).distinct()]
        existing_people_ids = {id[0] for id in db_session.query(People.id).all()}
        peoples_list = []
        BATCH_SIZE = 10000
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            with tqdm(total=len(people_ids), desc='Fetching People Details...') as pbar:
                futures = [executor.submit(fetch_people_data, pid) for pid in people_ids]
                for future in as_completed(futures):
                    people = future.result()
                    pbar.update(1)
                    if people and people.id not in existing_people_ids:
                        existing_people_ids.add(people.id)
                        peoples_list.append(people)
                    if len(peoples_list) >= BATCH_SIZE:
                        tqdm.write(f'Inserting {len(peoples_list)} people data into DB')
                        save_batch(peoples_list=peoples_list)
                        peoples_list.clear()
                if peoples_list:
                        tqdm.write(f'Inserting remaining people data into DB')
                        save_batch(peoples_list=peoples_list)
        print(f'Total People Fetched: {len(existing_people_ids)}')
        if failed_ids:
            print(f'Retry for Failed IDs: {failed_ids}')
    except Exception as e:
        db_session.rollback()
        print(f'[Exception]: {e}')
    finally:
        db_session.close()
        
if __name__ == "__main__":
    main()