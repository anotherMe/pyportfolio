
from datetime import timezone
from sqlalchemy import Column, DateTime, String, Integer, ForeignKey, Text, TypeDecorator, UniqueConstraint

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


# ==========================================================
# Type decorators
# ==========================================================


class UTCDateTime(TypeDecorator):
    """
    Custom SQLAlchemy type that enforces UTC timestamps.
    Guarantees all stored and loaded datetimes are timezone-aware and in UTC.
    """
    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        """
        When writing to DB:
            - Rejects naive datetimes.
            - Converts aware datetimes to UTC.
        """
        if value is None:
            return value
        if value.tzinfo is None:
            raise ValueError("naive datetime")
        return value.astimezone(timezone.utc)

    def process_result_value(self, value, dialect):
        """
        When reading from DB:
            - Attaches UTC tzinfo to returned values.
        """
        if value is None:
            return value
        return value.replace(tzinfo=timezone.utc)
    

# ==========================================================
#  Models
# ==========================================================


class Position(Base):
    __tablename__ = 'positions'
    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    instrument_id = Column(Integer, ForeignKey("instruments.id"), nullable=False)
    
    account = relationship("Account", back_populates="positions")
    instrument = relationship("Instrument", back_populates="positions")
    transactions = relationship("Transaction", back_populates="position", cascade="all")
    trades = relationship("Trade", back_populates="position", cascade="all")


class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    position_id = Column(Integer, ForeignKey("positions.id"), nullable=True)
    date = Column(UTCDateTime, nullable=False)
    type = Column(String, nullable=False)  # 'div', 'tax', 'fee'
    amount = Column(Integer, nullable=False)
    description = Column(Text)

    account = relationship("Account", back_populates="transactions")
    position = relationship("Position", back_populates="transactions")


class Price(Base):
    __tablename__ = "prices"
    id = Column(Integer, primary_key=True, autoincrement=True)
    instrument_id = Column(Integer, ForeignKey("instruments.id"), nullable=False)
    date = Column(UTCDateTime, nullable=False)
    price = Column(Integer, nullable=False)
    granularity = Column(String, nullable=False)

    instrument = relationship("Instrument", back_populates="prices")
    __table_args__ = (UniqueConstraint('instrument_id', 'date', 'granularity', name='_instrument_date_uc'),)


class OHLCV(Base):
    __tablename__ = 'ohlcvs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    instrument_id = Column(Integer, ForeignKey("instruments.id"), nullable=False)
    timestamp = Column(UTCDateTime, nullable=False)
    granularity = Column(String, nullable=False)
    open = Column(Integer)
    high = Column(Integer)
    low = Column(Integer)
    close = Column(Integer)
    volume = Column(Integer)

    instrument = relationship("Instrument", back_populates="ohlcvs")
    __table_args__ = (
        UniqueConstraint('instrument_id', 'timestamp', 'granularity', name='_instrument_timestamp_uc'),
)


class Instrument(Base):
    __tablename__ = "instruments"
    id = Column(Integer, primary_key=True, autoincrement=True)
    isin = Column(String, unique=True)
    ticker = Column(String)
    name = Column(String, nullable=False)
    name_long = Column(String)
    category = Column(String) # acc or dist
    description = Column(Text)
    currency = Column(String, nullable=False)

    trades = relationship("Trade", back_populates="instrument", cascade="all")
    prices = relationship("Price", back_populates="instrument", cascade="all")
    ohlcvs = relationship("OHLCV", back_populates="instrument", cascade="all")
    positions = relationship("Position", back_populates="instrument", cascade="all")


class Trade(Base):
    __tablename__ = "trades"
    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    position_id = Column(Integer, ForeignKey("positions.id"), nullable=False)
    instrument_id = Column(Integer, ForeignKey("instruments.id"), nullable=False)
    date = Column(UTCDateTime, nullable=False)
    type = Column(String, nullable=False)  # 'buy' or 'sell'
    quantity = Column(Integer, nullable=False)  # integer shares
    price = Column(Integer, nullable=False)
    description = Column(Text)

    account = relationship("Account", back_populates="trades")
    position = relationship("Position", back_populates="trades")
    instrument = relationship("Instrument", back_populates="trades")


class Account(Base):
    __tablename__ = "accounts"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(Text)

    transactions = relationship("Transaction", back_populates="account", cascade="all")
    trades = relationship("Trade", back_populates="account", cascade="all")
    positions = relationship("Position", back_populates="account", cascade="all")