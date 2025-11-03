
from enum import Enum

class TransactionType(Enum):
    FEE = "fee",
    DIVIDEND = "div",
    TAXES = "tax"

class TradeType(Enum):
    BUY = "buy"
    SELL = "sell"

class Currency(Enum):
    EUR = ("Euro", "€")
    USD = ("US Dollar", "$")
    GBP = ("British Pound", "£")
    JPY = ("Japanese Yen", "¥")

    def __init__(self, name, symbol):
        self.full_name = name
        self.symbol = symbol

    @classmethod
    def from_code(cls, code: str):
        try:
            return cls[code]
        except KeyError:
            return None
