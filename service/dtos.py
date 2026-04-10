"""
All Pydantic DTOs for the service layer.

Each DTO group mirrors one domain entity:
  - Account*      → accounts_service
  - Instrument*   → instruments_service
  - Trade*        → trades_service
  - Transaction*  → transactions_service
  - Position*     → positions_service
  - PriceDTO      → ohlcvs_service
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from lib.database import read_from_db
from lib.enums import AssetClass, Currency, DistributionPolicy, TradeType, TransactionType
from lib.models import Trade, Transaction


# ------------------------------------------------------------------
# Account
# ------------------------------------------------------------------

class AccountDTO(BaseModel):
    id: int
    name: str
    description: Optional[str] = None

    model_config = {"from_attributes": True}


class AccountCreateDTO(BaseModel):
    name: str
    description: Optional[str] = None


# ------------------------------------------------------------------
# Instrument
# ------------------------------------------------------------------

class InstrumentDTO(BaseModel):
    id: int
    name: str
    isin: Optional[str] = None
    ticker: Optional[str] = None
    name_long: Optional[str] = None
    dist_policy: Optional[DistributionPolicy] = None
    currency: Currency
    description: Optional[str] = None
    asset_class: Optional[AssetClass] = None

    model_config = {"from_attributes": True}


class InstrumentCreateDTO(BaseModel):
    name: str
    currency: Currency
    isin: Optional[str] = None
    ticker: Optional[str] = None
    name_long: Optional[str] = None
    dist_policy: Optional[DistributionPolicy] = None
    description: Optional[str] = None
    asset_class: Optional[AssetClass] = None


# ------------------------------------------------------------------
# Trade
# ------------------------------------------------------------------

class TradeDTO(BaseModel):
    """Full trade DTO with denormalized position/instrument fields for display."""
    id: int
    position_id: int
    account_id: int = 0
    account_name: str = ""
    instrument_id: int = 0
    instrument_name: str = ""
    instrument_isin: str = ""
    instrument_ticker: str = ""
    currency_symbol: str = ""
    date: datetime
    type: TradeType
    quantity: int
    price: float
    description: Optional[str] = None

    @classmethod
    def from_model(cls, trade: Trade) -> "TradeDTO":
        position = trade.position
        instrument = position.instrument
        return cls(
            id=trade.id,
            position_id=trade.position_id,
            account_id=position.account_id,
            account_name=position.account.name,
            instrument_id=instrument.id,
            instrument_name=instrument.name,
            instrument_isin=instrument.isin or "",
            instrument_ticker=instrument.ticker or "",
            currency_symbol=instrument.currency.symbol if instrument.currency else "",
            date=trade.date,
            type=trade.type,
            quantity=trade.quantity,
            price=read_from_db(trade.price),
            description=trade.description,
        )


class TradeCreateDTO(BaseModel):
    position_id: int
    date: datetime
    type: TradeType
    quantity: int
    price: float
    fee: float = 0.0
    description: Optional[str] = None


# ------------------------------------------------------------------
# Transaction
# ------------------------------------------------------------------

class TransactionDTO(BaseModel):
    """Full transaction DTO with denormalized account/instrument fields for display."""
    id: int
    account_id: int
    account_name: str = ""
    position_id: Optional[int] = None
    instrument_name: str = ""
    currency_symbol: str = ""
    date: datetime
    type: TransactionType
    amount: float
    description: Optional[str] = None

    @classmethod
    def from_model(cls, transaction: Transaction) -> "TransactionDTO":
        instrument_name = ""
        currency_symbol = "€"
        if transaction.position and transaction.position.instrument:
            instrument_name = transaction.position.instrument.name
            if transaction.position.instrument.currency:
                currency_symbol = transaction.position.instrument.currency.symbol
        return cls(
            id=transaction.id,
            account_id=transaction.account_id,
            account_name=transaction.account.name if transaction.account else "",
            position_id=transaction.position_id,
            instrument_name=instrument_name,
            currency_symbol=currency_symbol,
            date=transaction.date,
            type=transaction.type,
            amount=read_from_db(transaction.amount),
            description=transaction.description,
        )


class TransactionCreateDTO(BaseModel):
    account_id: int
    position_id: Optional[int] = None
    date: datetime
    type: TransactionType
    amount: float
    description: Optional[str] = None


# ------------------------------------------------------------------
# Position
# ------------------------------------------------------------------

class PositionDTO(BaseModel):
    """Full position summary with FIFO-computed P&L."""
    position_id: int

    instrument_id: int = 0
    instrument_name: str = ""
    instrument_isin: str = ""
    instrument_ticker: str = ""
    instrument_currency: str = ""
    instrument_symbol: str = ""

    opening_date: Optional[datetime] = None

    total_invested: float = 0.0

    latest_price: float = 0.0
    latest_price_date: Optional[datetime] = None

    transactions_amount: float = 0.0
    closing_date: Optional[datetime] = None
    remaining_quantity: int = 0
    remaining_cost_basis: float = 0.0

    realized_pnl: float = 0.0
    unrealized_pnl: float = 0.0
    realized_pnl_percent: float = 0.0
    unrealized_pnl_percent: float = 0.0

    model_config = {"arbitrary_types_allowed": True}


class PositionBasicDTO(BaseModel):
    """Lightweight position info for dropdowns and lists — no FIFO computation."""
    id: int
    account_id: int
    account_name: str
    instrument_id: int
    instrument_name: str
    instrument_ticker: str
    instrument_currency: str
    instrument_symbol: str

    model_config = {"from_attributes": True}


class PositionCreateDTO(BaseModel):
    account_id: int
    instrument_id: int


# ------------------------------------------------------------------
# Price (OHLCV)
# ------------------------------------------------------------------

class PriceDTO(BaseModel):
    instrument_id: int
    price: float
    date: Optional[datetime] = None

    model_config = {"arbitrary_types_allowed": True}
