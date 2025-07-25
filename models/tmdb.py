from sqlalchemy import Boolean, Column, Float, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from db.connect import Base

class MovieID(Base):
    __tablename__ = "movie_ids"
    id = Column(Integer, primary_key=True)

class Genre(Base):
    __tablename__ = "genre"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    movie_genres = relationship("MovieGenre", back_populates="genre", cascade="all, delete-orphan")

class Movie(Base):
    __tablename__ = "movie"
    id = Column(Integer ,primary_key=True)
    is_adult = Column(Boolean, default=False)
    language = Column(String)
    original_title = Column(String)
    overview = Column(Text)
    poster_path = Column(String)
    release_date = Column(String)
    runtime = Column(Integer)
    title = Column(String)
    status = Column(String)
    vote_average = Column(Float)

    credits = relationship("Credit", back_populates="movie", cascade="all, delete-orphan")
    movie_genres = relationship("MovieGenre", back_populates="movie", cascade="all, delete-orphan")

class MovieGenre(Base):
    __tablename__ = "movie_genre"
    genre_id = Column(Integer, ForeignKey('genre.id'), primary_key=True)
    movie_id = Column(Integer, ForeignKey('movie.id'), primary_key=True)

    genre = relationship("Genre", back_populates="movie_genres")
    movie = relationship("Movie", back_populates="movie_genres")

class Credit(Base):
    __tablename__ = "credit"
    id = Column(String, primary_key=True)
    movie_id = Column(Integer, ForeignKey('movie.id'))
    gender = Column(String)
    person_id = Column(Integer, ForeignKey('people.id'))
    name = Column(String)
    character_name = Column(String)

    movie = relationship("Movie", back_populates="credits")
    person = relationship("People", back_populates="credits")

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

    credits = relationship("Credit", back_populates="person", cascade="all, delete-orphan")
