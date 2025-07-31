from typing import List, Optional
from pydantic import BaseModel

class GenreResponse(BaseModel):
    id: int
    name: str

class MovieResponse(BaseModel):
    id: int
    is_adult: bool
    language: str
    original_title: str
    overview: str
    poster_path: Optional[str]
    release_date: str
    runtime: int
    title: str
    status: str
    vote_average: float

    model_config = {
        "from_attributes": True
    }

class CreditResponse(BaseModel):
    id: str
    movie_id: int
    gender: str
    person_id: int
    name: Optional[str]
    character_name: Optional[str]

    model_config = {
        "from_attributes": True
    }

class PeopleResponse(BaseModel):
    id: int
    is_adult: bool
    alias: Optional[List[str]]
    biography: Optional[str]
    gender: str
    name: str
    place_of_birth: Optional[str]
    profile_path: str

    model_config = {
        "from_attributes": True
    }

class PaginatedMovieResponse(BaseModel):
    total_count: int
    page: int
    page_size: int
    results: List[MovieResponse]

class PaginatedPeopleResponse(BaseModel):
    total_count: int
    page: int
    page_size: int
    results: List[PeopleResponse]