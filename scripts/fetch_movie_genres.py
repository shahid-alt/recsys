import random
import sys
import os
import time
import traceback

from tqdm import tqdm
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv
import requests
from db.connect import Base, engine, SessionLocal
from models.tmdb import MovieGenre

Base.metadata.create_all(bind=engine)
session = SessionLocal()


load_dotenv()
bearer_token = os.getenv("BEARER_TOKEN")
if not bearer_token:
    raise ValueError("Missing BEARER_TOKEN in .env")

endpoint = "https://api.themoviedb.org/3/genre/movie/list"

header = {
    "accept": "application/json",
    "Authorization": f"Bearer {bearer_token}"
}



def fetch_genres():
    try:
        response = requests.get(url=endpoint, headers=header)
        if response.status_code == 200:
                genres = response.json().get('genres', [])
                if not genres:
                        return []
                return genres
        else:
            print(f'TMDB Exception: {response.status_code} - {response.text}')
            return []
    except Exception as e:
        print(f"[Exception]: {e}")
        traceback.print_exc()

try:
    genres = []
    existing_genre_ids = {genre.id for genre in session.query(MovieGenre).all()}
    genres_result = fetch_genres()
    new_genres_list = []
    for genre in genres_result:
        new_genres_list = [
             MovieGenre(id=genre['id'], name=genre['name']) 
                for genre in genres_result 
                    if genre['id'] not in existing_genre_ids
        ]
    if new_genres_list:
            session.bulk_save_objects(new_genres_list)
            session.commit()
            print(f"Inserted {len(new_genres_list)} new genres.")
    else:
            print('No new Genres to insert in DB.')
except Exception as e:
    print(f"Exception Occured: {e}")
    session.rollback()
finally:
    session.close()
    