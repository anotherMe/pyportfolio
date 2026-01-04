import streamlit as st
import pandas as pd

from lib.database import get_session, read_from_db
from lib.repo.prices_repository import get_latest_prices_for_prices_list
from service.utils import to_local



st.title("📊 Latest Prices")

# Open a session
with get_session() as session:

    # Convert to DataFrame
    df = get_latest_prices_for_prices_list(session)
    df["last_close"] = df["last_close"].apply(lambda x: read_from_db(x) if x else None)
    df["instrument_ticker"] = df["instrument_ticker"].apply(lambda x: f"https://finance.yahoo.com/quote/{x}" if x else "")
    df["timestamp"] = df["timestamp"].apply(lambda x: to_local(x))

    # Show dataframe in Streamlit
    st.dataframe(
        df,
        column_config={
            "instrument_name": "Instrument",
            "instrument_ticker": st.column_config.LinkColumn(
                label="Ticker",
                help="Lookup ticker on Yahoo Finance site",
                display_text=r"/quote/([^/?#]+)"
            ),
            "last_close": st.column_config.NumberColumn(label="Last close", format="euro"), # FIXME: currency format should be dynamic
            "timestamp": st.column_config.DatetimeColumn(label="Timestamp"),
        },
        hide_index=True
    )   
