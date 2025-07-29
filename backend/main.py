from typing import Any, Dict, List, Optional
from fastapi import Depends, FastAPI, HTTPException, Query
from sqlalchemy import extract
from sqlalchemy.orm import Session
from db.connect import get_db
from models.tmdb import Credit, Genre, Movie, MovieGenre, People
app = FastAPI()

PAGE_SIZE = 20

@app.get('/')
def home():
    return {"message": "welcome, to tmdb"}

@app.get('/health')
def health_check() -> Dict[str, str]:
    return {"message": "ok"}

# Movie endpoints
# GET /movies/
# GET /movies/search/
# GET /movies/{movie_id}/
# GET /movies/{movie_id}/credits/
# GET /movies/{movie_id}/genres/

@app.get('/movies/')
def get_all_movies(
    page: int=Query(1, ge=1, description="Page Number Starts from 1"),
    db: Session=Depends(get_db)):
    query = db.query(Movie)
    if not query:
        raise HTTPException(404, "Resource Not Found", headers={"X-Error": "ResourceMissing"})
    

    total_count = query.count()
    offset = (page-1)*PAGE_SIZE
    results = query.limit(PAGE_SIZE).offset(offset).all()

    return {
        "total_count": total_count,
        "page": page,
        "page-size": PAGE_SIZE,
        "results": results
    }

@app.get('/movies/search/')
def search(
        query: Optional[str]=Query(None, description="Search by Title..."),
        genre: Optional[str]=Query(None, description="Search by Genre..."),
        year: Optional[int]=Query(None, description="Search by Release Year..."),
        status: Optional[str]=Query(None, description="Search by Status..."),
        language: Optional[str]=Query(None, description="Search by Language..."),
        page: int=Query(1, ge=1, description="Page Number, starts from 1"),
        db: Session=Depends(get_db)):
    
    q = db.query(Movie)
    if query:
        q = q.filter(Movie.title.ilike(f'%{query}%'))

    if genre:
        q = q.join(Movie.movie_genres).join(MovieGenre.genre).filter(Genre.name.ilike(f'%{genre}%'))
    
    if year:
        q = q.filter(extract('year', Movie.release_date) == year)

    if status:
        q = q.filter(Movie.status == status)

    if language:
        q = q.filter(Movie.language == language)

    total = q.count()
    offset = (page-1)*PAGE_SIZE
    results = q.limit(PAGE_SIZE).offset(offset).all()

    if not results:
        raise HTTPException(404, "Resource Not Found", headers={"X-Error": "ResourceMissing"})
    
    return {
        "results": results,
        "total_count": total,
        "page": page,
        "page-size": PAGE_SIZE
    }

@app.get('/movies/{movie_id}/')
def get_movie(movie_id: int, db: Session=Depends(get_db)):
    query: Movie|None = db.query(Movie).filter(Movie.id == movie_id).first()
    if not query:
        raise HTTPException(404, "Resource Not Found", headers={"X-Error": "ResourceMissing"})
    return {
        "result": query
    }

@app.get('/movies/{movie_id}/credits/')
def get_movie_credits(movie_id: int, db: Session=Depends(get_db)):
    query: Movie|None = db.query(Movie).filter(Movie.id == movie_id).first()
    if not query:
        raise HTTPException(404, "Resource Not Found", headers={"X-Error": "ResourceMissing"})
    
    credits = query.credits
    return {
        "result": credits
    }

@app.get('/movies/{movie_id}/genres#')
def get_movie_genres(movie_id: int, db: Session=Depends(get_db)):
    genres: List[Genre]|None = db.query(Genre).join(MovieGenre).filter(MovieGenre.movie_id == movie_id).all()
    if not genres:
        raise HTTPException(404, "Resource Not Found", headers={'X-Error': "ResourceMissing"})
    return {
        "result": genres
    }

# People Endpoints
# GET /people/
# GET /people/{person_id}
# GET /people/{person_id}/movies

@app.get('/people/')
def get_people(db: Session=Depends(get_db)):
    query: People|None = db.query(People).all()
    if not query:
        raise HTTPException(404, "Resource Not Found", headers={"X-Error": "ResourceMissing"})
    return {
        "result": query
    }

@app.get('/people/{person_id}/')
def get_person(person_id: int, db: Session=Depends(get_db)):
    query: People|None = db.query(People).filter(People.id == person_id).first()
    if not query:
        raise HTTPException(404, "Resource Not Found", headers={"X-Error": "ResourceMissing"})
    return {
        "result": query
    }

@app.get('/people/{person_id}/movies/')
def get_movies_for_person(person_id: int, db: Session=Depends(get_db)):
    query = db.query(Movie).join(Credit).filter(Credit.person_id == person_id).all()
    if not query:
        raise HTTPException(404, "Resource Not Found", headers={"X-Error": "ResourceMissing"})
    return {"result":  query}


# Genre Endpoints
# GET /genres/
# GET /genres/{genre_name}/movies/

@app.get('/genres/')
def get_all_genres(db:Session=Depends(get_db)):
    query = db.query(Genre).all()
    if not query:
        raise HTTPException(404, "Resource Not Found", headers={"X-Error": "ResourceMissing"})
    return {"result":  query}

@app.get('/genres/{genre_name}/')
def get_movies_by_genre_name(
                genre_name: str,
                db: Session=Depends(get_db),
                page: int=Query(1, ge=1, description='Page Number Starts from 1...')
            ):
    genre = db.query(Genre).filter(Genre.name.ilike(f'%{genre_name}%')).first()
    if not genre_name:
        raise HTTPException(404, "Resource Not Found", headers={"X-Error": "ResourceMissing"})
    movies = db.query(Movie)\
            .join(MovieGenre, Movie.id == MovieGenre.movie_id)\
            .filter(MovieGenre.genre_id == genre.id)
    total_count = movies.count()
    offset = (page-1)*PAGE_SIZE
    results = movies.limit(PAGE_SIZE).offset(offset).all()
    if not movies:
        raise HTTPException(404, "Resource Not Found", headers={"X-Error": "ResourceMissing"})
    
    return {
        "total_count": total_count,
        "page": page,
        "page-size": PAGE_SIZE,
        "results": results
    }