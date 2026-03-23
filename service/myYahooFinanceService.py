
"""

Load and parse a Yahoo Finance JSON file

"""


import traceback
import pandas as pd
import logging
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------
# Symbol Dataclass (with Streamlit helpers)
# ---------------------------------------------------------------------

@dataclass
class YahooSymbol:
    """Represent a Yahoo Finance symbol with metadata, price data, and events."""

    ticker: str
    name: str
    long_name: str
    currency: str
    data_granularity: str
    exchange_name: str
    full_exchange_name: str
    instrument_type: str
    gmtoffset: int
    timezone: str
    timezone_name: str
    ochlv_df: pd.DataFrame = field(default_factory=pd.DataFrame)
    events_df: Optional[pd.DataFrame] = None

    # Streamlit-friendly methods
    def to_dict(self) -> dict:
        """Convert the Symbol to a Streamlit-serializable dictionary."""
        return {
            "ticker": self.ticker,
            "name": self.name,
            "long_name": self.long_name,
            "currency": self.currency,
            "data_granularity": self.data_granularity,
            "exchange_name": self.exchange_name,
            "full_exchange_name": self.full_exchange_name,
            "instrument_type": self.instrument_type,
            "gmtoffset": self.gmtoffset,
            "timezone": self.timezone,
            "timezone_name": self.timezone_name,
            "ochlv_df": self.ochlv_df.to_dict(orient="list") if not self.ochlv_df.empty else None,
            "events_df": self.events_df.to_dict(orient="list") if self.events_df is not None else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "YahooSymbol":
        """Rebuild a Symbol object from a dictionary (e.g., from Streamlit session_state)."""
        ochlv_df = pd.DataFrame(data["ochlv_df"]) if data.get("ochlv_df") else pd.DataFrame()
        events_df = pd.DataFrame(data["events_df"]) if data.get("events_df") else None
        return cls(
            ticker=data["ticker"],
            name=data["name"],
            long_name=data["long_name"],
            currency=data["currency"],
            data_granularity=data["data_granularity"],
            exchange_name=data["exchange_name"],
            full_exchange_name=data["full_exchange_name"],
            instrument_type=data["instrument_type"],
            gmtoffset=data["gmtoffset"],
            timezone=data["timezone"],
            timezone_name=data["timezone_name"],
            ochlv_df=ochlv_df,
            events_df=events_df,
        )


# ---------------------------------------------------------------------
# YahooSymbolParser (auto-loads on init)
# ---------------------------------------------------------------------

class YahooSymbolParser:
    """Load and parse a Yahoo Finance JSON file into a Symbol object on initialization."""

    def __init__(self, data: str):
        self.data = data
        self.symbol: Optional[YahooSymbol] = None
        self._load()  # <-- auto-load immediately on instantiation

    def _load(self):
        """Internal: load and parse the JSON file into a Symbol dataclass."""


        if self.data["chart"]["error"] is not None:
            logger.error(f"Error in response: {self.data['chart']['error']}")
            return

        results = self.data["chart"].get("result", [])
        if len(results) != 1:
            logger.error("Wrong number of results found in the response.")
            return

        try:
            result = results[0]
            meta = result["meta"]

            # --- Build OCHLV DataFrame ---
            df = pd.DataFrame({"timestamp": result["timestamp"]})
            # df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s")
            df["timestamp"] = unix_to_datetime(df["timestamp"])

            quote = result["indicators"]["quote"][0]
            df["open"] = quote["open"]
            df["high"] = quote["high"]
            df["low"] = quote["low"]
            df["close"] = quote["close"]
            df["volume"] = quote["volume"]
            df["adjclose"] = result["indicators"]["adjclose"][0]["adjclose"]

            ochlv_df = df

            # --- Parse events (Dividends) ---
            events_df = None
            dividends_data = self.safe_get(result, ["events", "dividends"])
            if dividends_data:
                df = pd.DataFrame.from_dict(dividends_data, orient="index")
                df.index.name = "timestamp"
                df.reset_index(inplace=True)
                # df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s")
                df["timestamp"] = unix_to_datetime(df["timestamp"])
                # df["date"] = pd.to_datetime(df["date"], unit="s")
                df["date"] = unix_to_datetime(df["date"])
                events_df = df

            # --- Store Symbol object ---
            self.symbol = YahooSymbol(
                ticker=meta["symbol"],
                name=meta["shortName"],
                long_name=meta["longName"],
                currency=meta["currency"],
                data_granularity=meta["dataGranularity"],
                exchange_name=meta["exchangeName"],
                full_exchange_name=meta["fullExchangeName"],
                instrument_type=meta["instrumentType"],
                gmtoffset=meta["gmtoffset"],
                timezone=meta["timezone"],
                timezone_name=meta["exchangeTimezoneName"],
                ochlv_df=ochlv_df,
                events_df=events_df,
            )

        except Exception as e:
            logger.error(f"Error parsing JSON: {e}")
            print(traceback.format_exc())

    def safe_get(self, d, path, default=None):
        """Safely get nested dictionary/list values by following a path list."""
        current = d
        for p in path:
            if isinstance(current, dict):
                current = current.get(p, default)
            elif isinstance(current, list):
                try:
                    current = current[p]
                except (IndexError, TypeError):
                    return default
            else:
                return default
        return current

def unix_to_datetime(series, unit="s"):
    """
    Convert a pandas Series to datetime from Unix timestamps.
    Handles numeric or string representations of timestamps.
    
    Parameters:
        series (pd.Series): The column to convert.
        unit (str): Time unit of the timestamp ('s', 'ms', etc.).
        
    Returns:
        pd.Series: Datetime-converted Series.
    """
    # Ensure numeric type
    numeric_series = pd.to_numeric(series, errors="coerce")
    # Convert to datetime
    return pd.to_datetime(numeric_series, unit=unit)