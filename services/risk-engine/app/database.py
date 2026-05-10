import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:frauddefend@postgres:5432/fundguard")

engine = create_engine(
    DATABASE_URL, 
    pool_pre_ping=True,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db_session = scoped_session(SessionLocal)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
