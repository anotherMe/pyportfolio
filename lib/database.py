
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from lib.models import Base
from lib.settings_manager import get_db_path


# ==========================================================
# Dynamic database manager
# ==========================================================

_engine = None
_SessionLocal = None
_current_path = None


def init_engine():
    """(Re)initialize the SQLAlchemy engine based on current settings."""
    global _engine, _SessionLocal, _current_path

    db_path = get_db_path()

    # If the database path hasn't changed, don't recreate
    if db_path == _current_path and _engine is not None:
        return

    _engine = create_engine(db_path)
    _SessionLocal = sessionmaker(bind=_engine)
    _current_path = db_path
    print(f"✅ Database engine initialized at {db_path}")


def get_session():
    """Return a SQLAlchemy session; reinit engine if needed."""
    if _engine is None:
        init_engine()
    return _SessionLocal()

    
# ----------------------------------------------------------
# Utility functions
# ----------------------------------------------------------

def init_db():
    """Create all tables."""
    init_engine()
    Base.metadata.create_all(_engine)
    print(f"✅ Database schema created for {_current_path}")

def write_to_db(amount: float) -> int:
    return int(round(amount * 1000000))

def read_from_db(cents: int) -> float:
    return cents / 1000000

