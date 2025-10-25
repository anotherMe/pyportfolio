
import json
import traceback
import pandas as pd
import streamlit as st

from lib.database import get_session
from lib.myYahooFinance import YahooSymbolParser
from lib.repo.instruments_repository import get_all_instruments
from lib.repo.portfolio_repository import load_ohlcv_from_symbol
from lib.repo.prices_repository import get_latest_prices


st.title("Load Yahoo Finance data")

st.subheader("Instruments")

with get_session() as session:
    instruments = get_all_instruments(session)
    ohlcvs = get_latest_prices(session)

if not instruments:
    st.info("No instruments found.")
else:

    df_ohlcv = pd.DataFrame([
        {
            "instrument_id": o.instrument_id,
            "timestamp": o.timestamp,
            # "open": o.open,
            # "high": o.high,
            # "low": o.low,
            "close": o.close,
            # "volume": o.volume,
        }
        for o in ohlcvs
    ])

    df_instruments = pd.DataFrame([
        {
            "id": i.id,
            "ticker": i.ticker,
            "name": i.name,
            "name_long": i.currency,
        }
        for i in instruments
    ])

    # merge dataframes
    df = pd.merge(
        df_instruments,
        df_ohlcv,
        how="left",
        left_on="id",
        right_on="instrument_id"
    )

    # Add Yahoo finance link to ticker column
    df["ticker"] = df["ticker"].apply(
        lambda t: "https://finance.yahoo.com/quote/" + t.strip().upper() if t else ""
    )

    # --- Configure columns ---
    column_config = {
        "id": None,
        "name": st.column_config.TextColumn(label="Name", width="medium"),
        "name_long": None,
        # "Descr": st.column_config.TextColumn(width="large"),
        "instrument_id": None,
        "timestamp": st.column_config.DatetimeColumn(label="Latest price", width="large"),
        "close": None,
        "ticker": st.column_config.LinkColumn(
            label="Ticker",
            display_text=r"/quote/([^/?#]+)",
            width="small"
        ),
    }

    # --- Display table ---
    st.dataframe(
        data=df,
        hide_index=True,
        column_config=column_config,
    )



st.subheader("Load data")
create_instrument = st.checkbox("Create instrument if ticker does not exist")
uploaded_files = st.file_uploader("Choose one or more Yahoo Finance JSON files", type="json", accept_multiple_files=True)

for uploaded_file in uploaded_files:
    try:
        data = json.load(uploaded_file)
        parser = YahooSymbolParser(data)
        load_ohlcv_from_symbol(parser.symbol, create_instrument)
    except Exception as e:
        print(traceback.format_exc())
        st.error(f"Failed to load file: {uploaded_file.name}")
