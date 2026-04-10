
from datetime import datetime, timedelta
import pandas as pd
import streamlit as st
import time
import math

from lib.database import get_session
from lib.repo.ohlcvs_repository import get_latest_prices
from service.instruments_service import InstrumentsService
import service.YahooFinanceService as yfs
from service.custom_exceptions import PortfolioException
from service.utils import to_local

from logging_config import setup_logger
log = setup_logger(__name__)

instruments_service = InstrumentsService()

st.title("Prices")
st.subheader("Instruments latest update")

with get_session() as session:
    instruments = instruments_service.get_all(session)
    ohlcvs = get_latest_prices(session)

if not instruments:
    st.info("No instruments found.")
    st.stop()

df_ohlcv = pd.DataFrame([
    {
        "instrument_id": o.instrument_id,
        "timestamp": to_local(o.timestamp),
        "close": o.close,  # raw int — converted below after merge
    } for o in ohlcvs
])

df_instruments = pd.DataFrame([
    {
        "id": inst.id,
        "ticker": inst.ticker,
        "name": inst.name,
        "name_long": inst.name_long,
    } for inst in instruments
])

if not df_instruments.empty and not df_ohlcv.empty:
    from lib.database import read_from_db
    df_ohlcv["close"] = df_ohlcv["close"].apply(read_from_db)

    df = pd.merge(df_instruments, df_ohlcv, how="left", left_on="id", right_on="instrument_id")

    df["ticker"] = df["ticker"].apply(
        lambda t: "https://finance.yahoo.com/quote/" + t.strip().upper() if t else ""
    )

    column_config = {
        "id": None,
        "name": st.column_config.TextColumn(label="Name"),
        "name_long": None,
        "instrument_id": None,
        "timestamp": st.column_config.DatetimeColumn(label="Updated", format="YYYY-MM-DD"),
        "close": st.column_config.NumberColumn(label="Latest close", format="euro"),
        "ticker": st.column_config.LinkColumn(
            label="Ticker",
            display_text=r"/quote/([^/?#]+)",
            width="small",
        ),
    }

    st.dataframe(data=df, hide_index=True, column_config=column_config)


# --- Download from Yahoo Finance ---

st.subheader("Update prices data with yfinance")

message_container = st.empty()
progress_bar = st.progress(0, text="Idle")

with st.container(horizontal=True, horizontal_alignment="right"):
    btn_update_instruments = st.button(label="Download prices", type="primary")

if btn_update_instruments:
    # Need ORM objects for yfinance service (it reads .ticker attribute)
    with get_session() as session:
        from lib.repo.instruments_repository import get_all_instruments as _get_all_instruments
        from lib.repo.ohlcvs_repository import get_latest_prices as _get_latest_prices
        from lib.models import OHLCV
        orm_instruments = _get_all_instruments(session)
        orm_ohlcvs = _get_latest_prices(session)

        step = math.floor(100 / len(orm_instruments)) if orm_instruments else 100
        progress = 0
        for instrument in orm_instruments:
            latest_ohlcv = OHLCV()
            latest_ohlcv.timestamp = datetime.now() - timedelta(days=365)
            try:
                filtered = [o for o in orm_ohlcvs if o.instrument_id == instrument.id]
                latest_ohlcv = filtered[0]
            except Exception:
                log.warning(f"Cannot retrieve latest OHLCV for instrument {instrument.ticker}")

            progress += step
            progress_bar.progress(min(progress, 100), text="Operation in progress. Please wait.")
            success, message = yfs.download_history(instrument, latest_ohlcv.timestamp)
            with message_container:
                if success:
                    st.success(message)
                else:
                    st.error(message)
            time.sleep(1)
    progress_bar.empty()


# --- Load local JSON ---

st.subheader("Load data from local JSON")

uploaded_files = st.file_uploader("Load one or more local Yahoo Finance JSON files", type="json", accept_multiple_files=True)

col1, col2 = st.columns([1, 1])
with col1:
    create_instrument = st.checkbox("Create instrument if ticker does not exist")
with col2:
    with st.container(horizontal=True, horizontal_alignment="right"):
        btn_parse_files = st.button(label="Parse files", type="primary")

if btn_parse_files:
    for uploaded_file in uploaded_files:
        try:
            parser = yfs.parse_json_file_into_yahoo_symbol(uploaded_file)
            yfs.parse_file(parser, create_instrument)
            st.success(f"Parsed file {uploaded_file.name}")
        except PortfolioException:
            st.error(f"Error while parsing file {uploaded_file.name}")
            continue
