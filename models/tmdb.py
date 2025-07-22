from sqlalchemy import Boolean, Column, Float, Integer, String, Text
from db.connect import Base

class MovieID(Base):
    __tablename__ = "movie_ids"
    id = Column(Integer, primary_key=True)

class MovieGenre(Base):
    __tablename__ = "movie_genre"
    id = Column(Integer, primary_key=True)
    name = Column(String)

class Movie(Base):
    __tablename__ = "movie"
    id = Column(Integer, primary_key=True)
    is_adult = Column(Boolean, default=False)
    genres = Column(Text)
    language = Column(String)
    original_title = Column(String)
    overview = Column(Text)
    poster_path = Column(String)
    release_date = Column(String)
    runtime = Column(Integer)
    title = Column(String)
    status = Column(String)
    vote_average = Column(Float)

class Credit(Base):
    __tablename__ = "credit"
    id = Column(String, primary_key=True)
    movie_id = Column(Integer)
    gender = Column(String)
    person_id = Column(Integer)
    name = Column(String)
    character_name = Column(String)

class People(Base):
    __tablename__ = "people"
    id = Column(Integer, primary_key=True)
    is_adult = Column(Boolean)
    alias = Column(Text)
    biography = Column(Text)
    birthday = Column(String)
    gender = Column(String)
    name = Column(String)
    place_of_birth = Column(String)
    profile_path = Column(String)
