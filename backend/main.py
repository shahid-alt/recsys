import json
from typing import Any, Dict, List, Optional
from fastapi import Depends, FastAPI, HTTPException, Query
from sqlalchemy import extract
from sqlalchemy.orm import Session
from backend.schema import CreditResponse, GenreResponse, MovieResponse, PaginatedMovieResponse, PaginatedPeopleResponse, PeopleResponse
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
# GET /movies/{movie_id}/recommendations

@app.get('/movies/', response_model=PaginatedMovieResponse)
def get_all_movies(
    page: int=Query(1, ge=1, description="Page Number Starts from 1"),
    db: Session=Depends(get_db)):
    """
    Fetches all movies in paginated format (20 movies per page).

    Args:
        page (int): Page number to fetch (starts from 1).
        db (Session): SQLAlchemy database session.

    Returns:
        PaginatedMovieResponse: A paginated list of Movies

    Raises:
        HTTPException: If no movies exist in the database. 
    """
    query = db.query(Movie)    
    total_count = query.count()

    if total_count == 0:
        raise HTTPException(404, "Resource Not Found", headers={"X-Error": "ResourceMissing"})

    offset = (page-1)*PAGE_SIZE
    results = query.limit(PAGE_SIZE).offset(offset).all()

    return PaginatedMovieResponse(
        total_count=total_count,
        page=page,
        page_size=PAGE_SIZE,
        results=results
    )
    
@app.get('/movies/search/', response_model=PaginatedMovieResponse)
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

    total_count = q.count()
    offset = (page-1)*PAGE_SIZE
    results = q.limit(PAGE_SIZE).offset(offset).all()

    if not results:
        raise HTTPException(404, "Resource Not Found", headers={"X-Error": "ResourceMissing"})
    
    return PaginatedMovieResponse(
        total_count=total_count,
        page=page,
        page_size=PAGE_SIZE,
        results=results
    )

@app.get('/movies/{movie_id}/', response_model=MovieResponse)
def get_movie(movie_id: int, db: Session=Depends(get_db)):
    movie: Movie|None = db.query(Movie).filter(Movie.id == movie_id).first()
    if not movie:
        raise HTTPException(404, "Resource Not Found", headers={"X-Error": "ResourceMissing"})
    return movie

@app.get('/movies/{movie_id}/credits/', response_model=List[CreditResponse])
def get_movie_credits(movie_id: int, db: Session=Depends(get_db)):
    movie: Movie|None = db.query(Movie).filter(Movie.id == movie_id).first()
    if not movie:
        raise HTTPException(404, "Resource Not Found", headers={"X-Error": "ResourceMissing"})
    credits = movie.credits
    return credits

@app.get('/movies/{movie_id}/genres/', response_model=List[GenreResponse])
def get_movie_genres(movie_id: int, db: Session=Depends(get_db)):
    genres: List[Genre]|None = db.query(Genre).join(MovieGenre).filter(MovieGenre.movie_id == movie_id).all()
    if not genres:
        raise HTTPException(404, "Resource Not Found", headers={'X-Error': "ResourceMissing"})
    return genres

@app.get('/movies/{movie_id}/recommendations/')
def get_recommendation(movie_id: int, db: Session=Depends(get_db)):
    pass

# People Endpoints
# GET /people/
# GET /people/{person_id}
# GET /people/{person_id}/movies

@app.get('/people/', response_model=PaginatedPeopleResponse)
def get_people(db: Session=Depends(get_db), page: int=Query(1, ge=1, description='Page Number Starts from 1')):
    people: People|None = db.query(People)
    if not people:
        raise HTTPException(404, "Resource Not Found", headers={"X-Error": "ResourceMissing"})
    total_count = people.count()
    offset = (page-1)*PAGE_SIZE
    results = people.limit(PAGE_SIZE).offset(offset).all()

    for person in results:
        if isinstance(person.alias, str):
            try:
                person.alias = json.loads(person.alias)
            except Exception:
                person.alias = []

    return PaginatedPeopleResponse(
        total_count=total_count,
        page=page,
        page_size=PAGE_SIZE,
        results=results
    )

@app.get('/people/{person_id}/', response_model=PeopleResponse)
def get_person(person_id: int, db: Session=Depends(get_db)):
    person: People|None = db.query(People).filter(People.id == person_id).first()

    if isinstance(person.alias, str):
        try:
            person.alias = json.loads(person.alias)
        except Exception:
            person.alias = []

    if not person:
        raise HTTPException(404, "Resource Not Found", headers={"X-Error": "ResourceMissing"})
    return person

@app.get('/people/{person_id}/movies/', response_model=PaginatedMovieResponse)
def get_movies_for_person(person_id: int, db: Session=Depends(get_db),
                          page: int=Query(1, ge=1, description='Page Number Starts from 1')
                        ):
    movies = db.query(Movie).join(Credit).filter(Credit.person_id == person_id)
    total_count = movies.count()
    if total_count == 0:
        raise HTTPException(404, "Resource Not Found", headers={"X-Error": "ResourceMissing"})
    offset = (page-1)*PAGE_SIZE
    results = movies.limit(PAGE_SIZE).offset(offset).all()
    return PaginatedMovieResponse(
        total_count=total_count,
        page=page,
        page_size=PAGE_SIZE,
        results=results
    )

# Genre Endpoints
# GET /genres/
# GET /genres/{genre_name}/movies/

@app.get('/genres/', response_model=List[GenreResponse])
def get_all_genres(db:Session=Depends(get_db)):
    genres = db.query(Genre).all()
    if not genres:
        raise HTTPException(404, "Resource Not Found", headers={"X-Error": "ResourceMissing"})
    return genres

@app.get('/genres/{genre_name}/', response_model=PaginatedMovieResponse)
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
    
    return PaginatedMovieResponse(
        total_count=total_count,
        page=page,
        page_size=PAGE_SIZE,
        results=results
    )