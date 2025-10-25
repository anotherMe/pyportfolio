import streamlit as st
import pandas as pd

from lib.database import get_session, read_from_db
from lib.repo.ohlcvs_repository import get_latest_closing_prices

st.title("📊 Latest Prices")

# Open a session
with get_session() as session:
    results = get_latest_closing_prices(session)


# Convert to DataFrame
df = pd.DataFrame(results, columns=["instrument_name", "instrument_ticker", "last_close", "timestamp"])
df["last_close"] = df["last_close"].apply(lambda x: read_from_db(x) if x else None)
df["instrument_ticker"] = df["instrument_ticker"].apply(lambda x: f"https://finance.yahoo.com/quote/{x}" if x else "")

# Show dataframe in Streamlit
st.dataframe(
    df,
    column_config={
        "timestamp": st.column_config.DatetimeColumn(label="Timestamp"),
        "instrument_ticker": st.column_config.LinkColumn(
            help="Lookup ticker on Yahoo Finance site",
            display_text=r"/quote/([^/?#]+)"
        ),
    },
    hide_index=True
)
