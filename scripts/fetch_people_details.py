from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import os
from threading import Lock
import time
from typing import Optional

from dotenv import load_dotenv
import requests
from requests.adapters import HTTPAdapter
from requests.exceptions import SSLError
from urllib3.util.retry import Retry
from models.tmdb import Credit, People
from db.connect import SessionLocal
from utils.db_helpers import save_batch

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

def fetch_people_data(people_id: int) -> Optional[People]:
    """
    Fetches the details of the Cast using Unique ID of the person.

    Args:
        people_id (int): Unique ID of the cast in TMDB.

    Returns:
        Optional[People]: Object of the People having fields:
            - id (int): TMDB people ID.
            - is_adult (bool): Whether the cast is adult.
            - alias (list[str]): Other names of the Cast.
            - biography (str): Life summary of the person.
            - birthday (str): Date of Birth of person.
            - gender (int): Gender
            - name (str): Full Name of the person.
            - place_of_birth (str): Birth place of the person.
            - profile_path (str): Path of person's profile in TMDB.

    Raises: 
        SSLError: If any SSLError occurs.
        Exception: If any unexpected exception occurs.

    Notes:
        - Handles rate limiting (status code 429) with exponential backoff.
        - Returns None if the person is not found (status code 404).
    """
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

def main() -> None:
    """
    Fetches and saves the person information in the database.

    Workflow:
        1. Retrieves all the unique person IDs from database.
        2. Fetches the details of people in parallel using ThreadPoolExecutor.
        3. Batches and saves the people data in chunks of BATCH_SIZE in database.

    Notes:
        - Skips existing person ID to avoid duplication.
        - Logs progress and errors using tqdm.
    """
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
                        save_batch(peoples_list, session=db_session)
                        peoples_list.clear()
                if peoples_list:
                        tqdm.write(f'Inserting remaining people data into DB')
                        save_batch(records=peoples_list, session=db_session)
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