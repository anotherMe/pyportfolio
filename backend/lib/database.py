
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from lib.models import Base
from lib.settings_manager import get_db_path


# ==========================================================
# Dynamic database manager
# ==========================================================

DATABASE_URL = "sqlite:///../portfolio.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


# ----------------------------------------------------------
# Utility functions
# ----------------------------------------------------------

def write_to_db(amount: float) -> int:
    return int(round(amount * 1000000))

def read_from_db(cents: int) -> float:
    return cents / 1000000
