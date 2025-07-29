
# Movie Mirror API

A FastAPI-based backend API for a local movie database mirror with search, pagination, and genre filtering.  
Uses SQLAlchemy ORM for database models and Alembic for schema migrations.

---

## Features

- Browse movies with detailed metadata  
- Search movies by title, genre, year, status, and language  
- Pagination support with page numbers (20 results per page)  
- Filter movies by genre name  
- Robust SQL injection protection via SQLAlchemy ORM  
- Database schema managed using Alembic migrations

---

## Tech Stack

- Python 3.9+  
- FastAPI  
- SQLAlchemy ORM  
- Alembic (for DB migrations)  
- SQLite (default, can be configured to other DBs)  

---

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/movie-mirror-api.git
cd movie-mirror-api
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv
source venv/bin/activate    # Linux/macOS
venv\Scripts\activate       # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure database URL

Edit `alembic.ini` to set your database URL (default SQLite):

```
sqlalchemy.url = sqlite:///./movies.db
```

Or set environment variable (if supported):

```bash
export DATABASE_URL="sqlite:///./movies.db"
```

### 5. Run Alembic migrations

```bash
alembic upgrade head
```

### 6. Run the FastAPI server

```bash
uvicorn main:app --reload
```

---

## API Endpoints

- `GET /movies/` — List movies  
- `GET /movies/{movie_id}/` — Get movie details  
- `GET /movies/search/?page=1&query=batman` — Search movies with pagination  
- `GET /genres/{genre_name}/` — List movies by genre name  
- Additional endpoints: `/movies/{movie_id}/credits/`, `/movies/{movie_id}/genres/`

---

## Pagination

- Use the `page` query parameter to paginate results.  
- Each page returns 20 results.  
- Example: `/movies/search/?page=3&query=action`

---

## Testing for SQL Injection

- The API uses SQLAlchemy ORM to prevent SQL injection.  
- You can test with common injection payloads in query parameters; the API should respond safely without errors or unwanted data.

---

## Contributing

Feel free to open issues or submit pull requests!  
Make sure to run migrations after model changes:

```bash
alembic revision --autogenerate -m "Describe change"
alembic upgrade head
```

