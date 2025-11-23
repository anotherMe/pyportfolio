
from datetime import datetime, timedelta
import pandas as pd
import streamlit as st
import time
import math

from lib.database import get_session
from lib.models import OHLCV
from lib.repo.instruments_repository import get_all_instruments
from lib.repo.ohlcvs_repository import get_latest_prices
import service.YahooFinanceService as yfs
from service.custom_exceptions import PortfolioException

from logging_config import setup_logger
from service.utils import to_local
log = setup_logger(__name__)


st.title("Load Yahoo Finance data")

st.subheader("Instruments latest update")

with get_session() as session:
    instruments = get_all_instruments(session)
    ohlcvs = get_latest_prices(session)


# ----------------------------------------------------------------------------------------------------------------------------
# Instrument list

if not instruments:
    st.info("No instruments found.")
else:

    df_ohlcv = pd.DataFrame([
        {
            "instrument_id": o.instrument_id,
            "timestamp": to_local(o.timestamp),
            # "open": o.open,
            # "high": o.high,
            # "low": o.low,
            "close": o.close,
            # "volume": o.volume,
        } for o in ohlcvs
    ])

    df_instruments = pd.DataFrame([
        {
            "id": i.id,
            "ticker": i.ticker,
            "name": i.name,
            "name_long": i.currency,
        } for i in instruments
    ])

    if not df_instruments.empty and not df_ohlcv.empty:

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


# ----------------------------------------------------------------------------------------------------------------------------
# Download from Yahoo Finance

st.subheader("Update prices data with yfinance")

message_container = st.container()
progress_bar = st.progress(0, text="Idle")

col1, col2 = st.columns([5,1])
with col2:
    btn_update_instruments = st.button(label="Download prices", type="primary")

if btn_update_instruments:

    step = math.floor(100 / len(instruments))
    progress = 0
    for instrument in instruments:

        # retrive latest available OHLCV for instrument
        latest_ohlcv = OHLCV()
        latest_ohlcv.timestamp = datetime.now() - timedelta(days=365) # Set to one year ago
        try:
            filtered_ohlcvs = [o for o in ohlcvs if o.instrument_id == instrument.id]
            latest_ohlcv = filtered_ohlcvs[0]
        except Exception:
            # There was an error or simply we have no OHLCVs yet for the current instrument
            log.warning(f"Cannot retrieve latest OHLCV for instrument {instrument.ticker}")

        progress += step
        progress_bar.progress(progress, text="Operation in progress. Please wait.")
        success, message = yfs.download_history(instrument, latest_ohlcv.timestamp)
        with message_container:
            if success:
                st.success(message)
            else:
                st.error(message)
        time.sleep(5)
    progress_bar.empty()



# ----------------------------------------------------------------------------------------------------------------------------
# Load local JSON (Yahoo Finance)


st.subheader("Load data from local JSON")

uploaded_files = st.file_uploader("Load one or more local Yahoo Finance JSON files", type="json", accept_multiple_files=True)

col1, col2 = st.columns([5,1])
with col1:
    create_instrument = st.checkbox("Create instrument if ticker does not exist")
with col2:
    btn_parse_files =  st.button(label="Parse files", type="primary")

if btn_parse_files:
    for uploaded_file in uploaded_files:

        try:
            parser = yfs.parse_json_file_into_yahoo_symbol(uploaded_file)
            yfs.parse_file(parser, create_instrument)
            st.success(f"Parsed file {uploaded_file.name}")
        except PortfolioException:
            st.error(f"Error while parsing file {uploaded_file.name}")
            continue