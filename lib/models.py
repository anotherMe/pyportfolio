
from sqlalchemy import Boolean, Column, DateTime, String, Integer, ForeignKey, Text, UniqueConstraint

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

from lib.types import UTCDateTime, CurrencyType

Base = declarative_base()


# ==========================================================
#  Models
# ==========================================================


class Position(Base):
    __tablename__ = 'positions'
    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    instrument_id = Column(Integer, ForeignKey("instruments.id"), nullable=False)
    closed = Column(Boolean, nullable=False)
    closing_date = Column(UTCDateTime)
    
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
    __table_args__ = (UniqueConstraint('instrument_id', 'timestamp', 'granularity', name='_instrument_timestamp_uc'),)


class Instrument(Base):
    __tablename__ = "instruments"
    id = Column(Integer, primary_key=True, autoincrement=True)
    isin = Column(String)
    ticker = Column(String)
    name = Column(String, nullable=False)
    name_long = Column(String)
    category = Column(String) # acc or dist
    description = Column(Text)
    currency = Column(CurrencyType, nullable=False)

    prices = relationship("Price", back_populates="instrument", cascade="all")
    ohlcvs = relationship("OHLCV", back_populates="instrument", cascade="all")
    positions = relationship("Position", back_populates="instrument", cascade="all")


class Trade(Base):
    __tablename__ = "trades"
    id = Column(Integer, primary_key=True, autoincrement=True)
    position_id = Column(Integer, ForeignKey("positions.id"), nullable=False)
    date = Column(UTCDateTime, nullable=False)
    type = Column(String, nullable=False)  # 'buy' or 'sell'
    quantity = Column(Integer, nullable=False)  # integer shares
    price = Column(Integer, nullable=False)
    description = Column(Text)

    position = relationship("Position", back_populates="trades")


class Account(Base):
    __tablename__ = "accounts"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(Text)

    transactions = relationship("Transaction", back_populates="account", cascade="all")
    positions = relationship("Position", back_populates="account", cascade="all")