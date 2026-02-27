import streamlit as st

from lib.database import get_session, read_from_db
from lib.repo.prices_repository import get_latest_prices_for_prices_list
from service.utils import to_local



st.title("📊 Latest Prices")

# Open a session
with get_session() as session:

    # Convert to DataFrame
    df = get_latest_prices_for_prices_list(session)
    
    # Format the price with the dynamically queried currency symbol
    df["last_close_styled"] = df.apply(
        lambda row: f"{read_from_db(row['last_close']):,.2f} {row['instrument_symbol']}" if row['last_close'] else "", 
        axis=1
    )
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
            "instrument_currency": None, # Hide intermediate data
            "instrument_symbol": None,
            "last_close": None, # Hide raw number column
            "last_close_styled": "Last close",
            "timestamp": st.column_config.DatetimeColumn(label="Timestamp", format="YYYY-MM-DD"),
        },
        hide_index=True
    )   
