
from enum import Enum


class TransactionType(Enum):
    FEE = "fee"
    DIVIDEND = "div"
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


class DistributionPolicy(Enum):
    ACCUMULATING = "acc"
    DISTRIBUTING = "dist"


class AssetClass(Enum):
	EQUITY = "Equity"
	BONDS = "Bonds"
	PRECIOUS = "Precious metals"
	COMMODITIES = "Commodities"
	CRYPTO = "Cryptocurrencies"
	RE = "Real estate"
	MONEY = "Money market"


class OHLCVGranularity(Enum):
    DAY = "1d"
    WEEK = "1wk"
    MONTH = "1mo"
