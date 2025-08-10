import os
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()
db_path = os.getenv('DB_PATH')
DATABASE_URL = f"sqlite:///{os.path.abspath(db_path)}"

engine = create_engine(
    DATABASE_URL,
    connect_args={
        "check_same_thread": False,
        "timeout": 30               
    },
    pool_size=5,
    max_overflow=10,                
    pool_timeout=30,                 
    echo=False                   
)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

def init_db():
    Base.metadata.create_all(bind=engine)

init_db()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()