import json
from math import ceil
import os
from typing import Any, Dict, List, Optional
from fastapi import Depends, FastAPI, HTTPException, Query
from sqlalchemy import extract, func
from sqlalchemy.orm import Session
from backend.schema import CreditResponse, GenreResponse, MovieResponse, PaginatedMovieResponse, PaginatedPeopleResponse, PeopleResponse
from db.connect import get_db
from models.tmdb import Credit, Genre, Movie, MovieGenre, People
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()
FRONTEND_URL = os.getenv("FRONTEND_URL")
allowed_origins = None
if not FRONTEND_URL:
    allowed_origins = ["*"]
    print('FRONTEND_URL value missing in .env')
else:
    allowed_origins = [FRONTEND_URL]

app = FastAPI()
# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
        raise HTTPException(404, "No movies found in the database", headers={"X-Error": "ResourceMissing"})

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
    """
    Fetches the movies using various filters (20 movies per page)

    Args: 
        query (str): Search movies by title name
        genre (str): Search movies by genre name (e.g Drama, Thriller, etc.)
        year (str): Search movies by year of release
        status (str): Search movies by the status of movie (e.g Released, In Production, etc.)
        language (str): Search movies by language (e.g en, de, etc.)
        page (int): Page number to fetch (Number starts from 1)
        db (Session): SQLAlchemy database session

    Returns:
        PaginatedMovieResponse: A paginated list of movies

    Raises:
        HTTPException: If no movies exist in database with applied filters
        HTTPException: If page number exceeds maximum limit
    """
    q = db.query(Movie)
    if query:
        query = query.strip()
        q = q.filter(Movie.title.ilike(f'%{query}%'))

    if genre:
        q = q.join(Movie.movie_genres).join(MovieGenre.genre).filter(Genre.name == genre)

    if year:
        q = q.filter(Movie.release_date != None)
        q = q.filter(extract('year', Movie.release_date) == year)

    if status:
        status = status.strip()
        q = q.filter(func.lower(Movie.status) == status.lower())

    if language:
        q = q.filter(func.lower(Movie.language) == language.lower())

    total_count = q.count()
    if total_count == 0:
        raise HTTPException(404, "Resource Not Found with applied filters", headers={"X-Error": "ResourceMissing"})

    total_pages = ceil(total_count/PAGE_SIZE)
    if page > total_pages:
        raise HTTPException(404, f"Page out of Range, Page should be lesser than {total_pages}")
    
    q = q.order_by(Movie.release_date.desc(), Movie.title.asc())
    offset = (page-1)*PAGE_SIZE
    results = q.limit(PAGE_SIZE).offset(offset).all()
    
    return PaginatedMovieResponse(
        total_count=total_count,
        page=page,
        page_size=PAGE_SIZE,
        results=results
    )

@app.get('/movies/{movie_id}/', response_model=MovieResponse)
def get_movie(movie_id: int, db: Session=Depends(get_db)):
    """
    Fetch movie details by movie ID.

    Args:
        movie_id (int): Unique ID of the movie to retrieve
        db (Session): SQLAlchemy database session

    Returns:
        MovieResponse: Serialized movie data

    Raises:
        HTTPException: If no movie is found with the provided ID     
    """
    movie: Movie|None = db.query(Movie).filter(Movie.id == movie_id).one_or_none()
    if not movie:
        raise HTTPException(
                        404, 
                        f"Movie with ID: {movie_id} not found", 
                        headers={"X-Error": "ResourceMissing"}
                    )
    return movie

@app.get('/movies/{movie_id}/credits/', response_model=List[CreditResponse])
def get_movie_credits(movie_id: int, db: Session=Depends(get_db)):
    """
    Fetch credits of movie by Movie ID

    Args:
        movie_id (int): Unique ID of the movie
        db (Session): SQLAlchemy database session

    Returns:
        List[CreditResponse]: A list of credit entries for the movie

    Raises:
        HTTPException: If no movie is found with provided ID
    """
    movie: Movie|None = db.query(Movie).filter(Movie.id == movie_id).one_or_none()
    if not movie:
        raise HTTPException(404, f"Movie with ID: {movie_id} not found", headers={"X-Error": "ResourceMissing"})
    credits = movie.credits
    return credits

@app.get('/movies/{movie_id}/genres/')
def get_movie_genres(movie_id: int, db: Session=Depends(get_db)):
    """
    Fetches the genres of the given movie by its ID

    Args:
        movie_id (int): Unique ID of the movie
        db (Session): SQLAlchemy database session

    Returns:
        List[GenreResponse]: A list of all the genres for the movie

    Raises:
        HTTPException: If no genres do not exist for the given movie
    """
    genres: List[Genre]|None = db.query(Genre).join(MovieGenre).filter(MovieGenre.movie_id == movie_id).all()
    if not genres:
        raise HTTPException(404, f"Movie with ID: {movie_id} not found", headers={'X-Error': "ResourceMissing"})
    return genres

@app.get('/movies/{movie_id}/recommendations/')
def get_recommendation(movie_id: int, db: Session=Depends(get_db)):
    pass

# People Endpoints
# GET /people/
# GET /people/{person_id}
# GET /people/{person_id}/movies

@app.get('/people/', response_model=PaginatedPeopleResponse)
def get_people(page: int=Query(1, ge=1, description='Page Number Starts from 1'), db: Session=Depends(get_db)):
    """
    Fetches the details of all people in database (20 people per page)

    Args:
        page (int): Page number to fetch (Starts from 1)
        db (Session): SQLAlchemy database session

    Returns:
        PaginatedPeopleResponse: Paginated list of People

    Raises:
        HTTPException: If no people exist in the database
        HTTPException: If page number exceeds the maximum pages limit
    """
    people: People|None = db.query(People)
    total_count = people.count()
    if total_count == 0:
        raise HTTPException(404, "No People found in the database", headers={"X-Error": "ResourceMissing"})
    
    total_pages = ceil(total_count/PAGE_SIZE)
    if page > total_pages:
        raise HTTPException(
                404, 
                f"Page number out of range, Maximum allowed pages is {total_pages}",
                headers={"X-Error": "ResourceMissing"}
            )
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
    """
    Fetch details of a person by their ID

    Args:
        person_id (int): Unique ID of the People to retreive
        db (Session): SQLAlchemy database session

    Returns:
        PeopleResponse: Serialized data of people with given ID

    Raises:
        HTTPException: If person with people ID is not found
    """
    person: People|None = db.query(People).filter(People.id == person_id).one_or_none()
    if not person:
        raise HTTPException(404, f"Person with ID: {person_id} not found", headers={"X-Error": "ResourceMissing"})

    if isinstance(person.alias, str):
        try:
            person.alias = json.loads(person.alias)
        except Exception:
            person.alias = []

    return person

@app.get('/people/{person_id}/movies/', response_model=PaginatedMovieResponse)
def get_movies_for_person(
                        person_id: int, 
                        page: int=Query(1, ge=1, description='Page Number Starts from 1'),
                        db: Session=Depends(get_db)
                    ):
    """
    Fetches movies of the people by person ID (Max 20 movies per page)

    Args:
        person_id (int): Unique ID of the People
        page (int): Page Number to fetch (Page number starts from 1)
        db (Session): SQLAlchemy database session

    Returns:
        PaginatedMovieResponse: Paginated list of movies

    Raises:
        HTTPException: If no people exists with provided person ID

    """
    movies = db.query(Movie).join(Credit).filter(Credit.person_id == person_id)
    total_count = movies.count()
    if total_count == 0:
        raise HTTPException(404, f"Person with ID: {person_id} not found", headers={"X-Error": "ResourceMissing"})
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
    """
    Fetches all the genres in the database

    Args:
        db (Session): SQLAlchemy database session

    Returns: 
        List[GenreResponse]: List of the genres in the database

    Raises:
        HTTPException: If no genres exist in the database
    """
    genres: List[Genre] = db.query(Genre).order_by(Genre.id).all()
    if not genres:
        raise HTTPException(404, "Genres Not Found", headers={"X-Error": "ResourceMissing"})
    return genres

@app.get('/genres/{genre_name}/', response_model=PaginatedMovieResponse)
def get_movies_by_genre_name(
                genre_name: str,
                page: int=Query(1, ge=1, description='Page Number Starts from 1...'),
                db: Session=Depends(get_db)
            ):
    """
    Fetches all the movies having provided genre name

    Args:
        genre_name (str): Genre name of the movies to retrieve
        page (int): Page number to fetch (Page number starts from 1)
        db (Session): SQLAlchemy database session

    Returns:
        PaginatedMovieResponse: Paginated list of movies of genre name provided

    Raises:
        HTTPException: If no genre name is found in the database
        HTTPException: If page number exceeds the maximum range
        HTTPException: If movies are not found with the given genre name
    """
    genre = db.query(Genre).filter(Genre.name.ilike(f'%{genre_name}%')).one_or_none()
    if not genre:
        raise HTTPException(404, f"Genre `{genre_name}` is not found", headers={"X-Error": "ResourceMissing"})
    
    movies = db.query(Movie)\
            .join(MovieGenre, Movie.id == MovieGenre.movie_id)\
            .filter(MovieGenre.genre_id == genre.id)
    
    total_count = movies.count()
    if total_count == 0:
        raise HTTPException(404, f"No movies found with genre `{genre_name}`", headers={"X-Error": "ResourceMissing"})

    total_pages = ceil(total_count/PAGE_SIZE)
    if page > total_pages:
        raise HTTPException(
                404, 
                f"Page number out of range, Maximum allowed pages is {total_pages}",
                headers={"X-Error": "ResourceMissing"}
            )
    
    offset = (page-1)*PAGE_SIZE
    movies = movies.order_by(Movie.release_date.desc(), Movie.title.asc())
    results = movies.limit(PAGE_SIZE).offset(offset).all()
    
    return PaginatedMovieResponse(
        total_count=total_count,
        page=page,
        page_size=PAGE_SIZE,
        results=results
    )