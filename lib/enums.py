
from enum import Enum

class TransactionType(Enum):
    FEE = "fee",
    DIVIDEND = "div",
    TAXES = "tax"

class TradeType(Enum):
    BUY = "buy"
    SELL = "sell"