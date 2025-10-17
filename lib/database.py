
from click import echo
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from lib.models import Base


DB_PATH = "sqlite:///portfolio.db"
engine = create_engine(DB_PATH)
SessionLocal = sessionmaker(bind=engine, )

def get_session():
    return SessionLocal()

def init_db():
    Base.metadata.create_all(engine)
    print(f"✅ Database initialized at {DB_PATH}")


# ----------------------------------------------------------
# Utility functions
# ----------------------------------------------------------

def to_cents(amount: float) -> int:
    return int(round(amount * 100))

def from_cents(cents: int) -> float:
    return cents / 100


