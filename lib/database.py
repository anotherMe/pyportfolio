
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from lib.models import Base
import streamlit as st


DB_PATH = "sqlite:///portfolio.db"
engine = create_engine(DB_PATH, echo=False)
SessionLocal = sessionmaker(bind=engine)



@st.cache_resource
def get_engine():
    # For SQLite; adapt for PostgreSQL/MySQL if needed
    return create_engine("sqlite:///portfolio.db", connect_args={"check_same_thread": False})

# Each thread (i.e., each Streamlit session) gets its own session
@st.cache_resource
def get_session_factory():
    engine = get_engine()
    return sessionmaker(bind=engine, autocommit=False, autoflush=False)

@contextmanager
def get_session():
    """Thread-safe session context for Streamlit."""
    SessionLocal = get_session_factory()
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
        
def init_db():
    Base.metadata.create_all(engine)
    print(f"✅ Database initialized at {DB_PATH}")

# ----------------------------------------------------------
# Cents conversion
# ----------------------------------------------------------
def to_cents(amount: float) -> int:
    return int(round(amount * 100))

def from_cents(cents: int) -> float:
    return cents / 100


