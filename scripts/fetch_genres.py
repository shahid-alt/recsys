import os
import traceback
from typing import List
from dotenv import load_dotenv
import requests
from db.connect import Base, engine, SessionLocal
from models.tmdb import Genre

session = SessionLocal()


load_dotenv()
bearer_token = os.getenv("BEARER_TOKEN")
if not bearer_token:
    raise ValueError("Missing BEARER_TOKEN in .env")

header = {
    "accept": "application/json",
    "Authorization": f"Bearer {bearer_token}"
}

def fetch_genres(endpoints: List[str]):
    if endpoints:
        for url in endpoints:
            try:
                response = requests.get(url=url, headers=header)
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
    else:
         print("Endpoint List is empty")

def main():
    try:
        endpoints = [
             "https://api.themoviedb.org/3/genre/movie/list",
             "https://api.themoviedb.org/3/genre/tv/list"
        ]
        
        existing_genre_ids = {genre.id for genre in session.query(Genre).all()}
        genres_result = fetch_genres(endpoints=endpoints)
        new_genres_list = []
        for _genre in genres_result:
            new_genres_list = [Genre(id=genre['id'], name=genre['name']) for genre in genres_result if genre['id'] not in existing_genre_ids]
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


if __name__ == "__main__":
     main()
        