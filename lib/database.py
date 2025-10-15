
from sqlalchemy import create_engine, func, case, desc
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from lib.models import Base, Instrument, Trade, MarketPrice, Transaction

DB_PATH = "sqlite:///portfolio.db"
engine = create_engine(DB_PATH, echo=False)
SessionLocal = sessionmaker(bind=engine)

def init_db():
    Base.metadata.create_all(engine)
    print(f"✅ Database initialized at {DB_PATH}")

def get_session():
    return SessionLocal()

# ----------------------------------------------------------
# Cents conversion
# ----------------------------------------------------------
def to_cents(amount: float) -> int:
    return int(round(amount * 100))

def from_cents(cents: int) -> float:
    return cents / 100



