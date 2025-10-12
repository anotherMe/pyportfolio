from sqlalchemy import (
    Column, String, Integer, DateTime, ForeignKey, Text, UniqueConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

# ==========================================================
#  Market Data
# ==========================================================
class OHLCV(Base):
    __tablename__ = 'ohlcv'
    symbol = Column(String, primary_key=True)
    timestamp = Column(DateTime, primary_key=True)
    granularity = Column(String, nullable=False)
    open = Column(Integer)   # in cents
    high = Column(Integer)
    low = Column(Integer)
    close = Column(Integer)
    volume = Column(Integer)
    __table_args__ = (
        UniqueConstraint('symbol', 'timestamp', name='_symbol_timestamp_uc'),
    )

# ==========================================================
#  Instruments
# ==========================================================
class Instrument(Base):
    __tablename__ = "instruments"
    id = Column(Integer, primary_key=True, autoincrement=True)
    isin = Column(String, unique=True, nullable=False)
    ticker = Column(String)
    name = Column(String, nullable=False)
    category = Column(String)
    currency = Column(String, default="EUR")

    trades = relationship("Trade", back_populates="instrument", cascade="all, delete-orphan")
    prices = relationship("MarketPrice", back_populates="instrument", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="instrument", cascade="all, delete-orphan")

# ==========================================================
#  Trades (Buy/Sell)
# ==========================================================
class Trade(Base):
    __tablename__ = "trades"
    id = Column(Integer, primary_key=True, autoincrement=True)
    instrument_id = Column(Integer, ForeignKey("instruments.id", ondelete="CASCADE"), nullable=False)
    date = Column(DateTime, nullable=False)
    type = Column(String, nullable=False)  # 'buy' or 'sell'
    quantity = Column(Integer, nullable=False)  # integer shares
    price = Column(Integer, nullable=False)     # in cents
    fees = Column(Integer, default=0)           # in cents
    description = Column(Text)
    instrument = relationship("Instrument", back_populates="trades")

# ==========================================================
#  Market Prices
# ==========================================================
class MarketPrice(Base):
    __tablename__ = "market_prices"
    id = Column(Integer, primary_key=True, autoincrement=True)
    instrument_id = Column(Integer, ForeignKey("instruments.id", ondelete="CASCADE"), nullable=False)
    date = Column(DateTime, nullable=False)
    price = Column(Integer, nullable=False)   # in cents
    instrument = relationship("Instrument", back_populates="prices")
    __table_args__ = (UniqueConstraint('instrument_id', 'date', name='_instrument_date_uc'),)

# ==========================================================
#  Transactions (Dividends, Taxes, Fees)
# ==========================================================
class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    instrument_id = Column(Integer, ForeignKey("instruments.id", ondelete="CASCADE"), nullable=True)
    date = Column(DateTime, nullable=False)
    type = Column(String, nullable=False)  # 'dividend', 'tax', 'fee', 'global_tax'
    amount = Column(Integer, nullable=False)  # in cents
    description = Column(Text)
    instrument = relationship("Instrument", back_populates="transactions")
