
from datetime import datetime, timedelta
import pandas as pd
import streamlit as st
import time
import math

from lib.database import get_session
from lib.database import read_from_db
from service.instruments_service import InstrumentsService
from service.ohlcvs_service import OhlcvsService
import service.YahooFinanceService as yfs
from service.custom_exceptions import PortfolioException
from service.utils import to_local
from lib.models import OHLCV
import plotly.graph_objects as go

from logging_config import setup_logger
log = setup_logger(__name__)

instruments_service = InstrumentsService()
ohlcvs_service = OhlcvsService()


st.title("Prices")
st.subheader("Instruments latest update")

with get_session() as session:
    instruments = instruments_service.get_all(session)
    ohlcvs = ohlcvs_service.get_latest_prices(session)

if not instruments:
    st.info("No instruments found.")
    st.stop()

df_ohlcv = pd.DataFrame([
    {
        "instrument_id": o.instrument_id,
        "timestamp": to_local(o.date),
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

    st_dataframe = st.dataframe(
        data=df,
        hide_index=True,
        column_config=column_config,
        on_select="rerun",
        selection_mode="single-row",
        key="prices_dataframe",
    )

    selected_rows = st_dataframe.selection.rows  # type: ignore[union-attr]
    if selected_rows:
        selected_row = df.iloc[selected_rows[0]]
        selected_inst = next(i for i in instruments if i.id == selected_row["id"])

        with st.container(border=True):
            st.subheader(selected_inst.name)
            if selected_inst.name_long:
                st.markdown(f"**{selected_inst.name_long.strip()}**")
            col1, col2 = st.columns([2, 1])
            if selected_inst.isin:
                col1.write(f"**ISIN:** [{selected_inst.isin}](https://www.justetf.com/en/etf-profile.html?isin={selected_inst.isin})")
                col1.write(f"**Last updated :** {pd.Timestamp(selected_row['timestamp']).strftime('%Y-%m-%d')}")
            if selected_inst.ticker:
                col2.write(f"**Ticker:** [{selected_inst.ticker}](https://finance.yahoo.com/quote/{selected_inst.ticker})")

            st.space()
            col1, col2, col3 = st.columns([2, 2, 1], vertical_alignment="bottom")
            period = col1.selectbox(
                "Period",
                options=["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"],
                index=10,
                key="dl_period",
            )
            interval = col2.selectbox(
                "Interval",
                options=["1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h", "1d", "5d", "1wk", "1mo", "3mo"],
                index=8,
                key="dl_interval",
            )
            if col3.button("Download", type="primary", key="dl_button"):
                with st.spinner(f"Downloading {selected_inst.ticker}…"):
                    with get_session() as session:
                        orm_inst = instruments_service.get_by_ticker(session, selected_inst.ticker) if selected_inst.ticker else None
                    if orm_inst:
                        success, message = yfs.download_history_with_period(orm_inst, period, interval)
                        if success:
                            st.success(message)
                        else:
                            st.error(message)

        st.space()
        with st.container(border=True):
            with get_session() as session:
                prices_list = ohlcvs_service.get_prices_for_instrument(session, selected_inst.id)

            if prices_list:
                
                prices_df = pd.DataFrame([p.model_dump(mode="json") for p in prices_list])
                fig = go.Figure(data=go.Ohlc(
                    x=prices_df['date'],
                    open=prices_df['open'],
                    high=prices_df['high'],
                    low=prices_df['low'],
                    close=prices_df['close'],
                ))
                fig.update_layout(
                    title=f"{selected_inst.name} — Price History",
                    xaxis_title="Date",
                    yaxis_title="Price",
                    height=800,
                    hovermode="x unified",
                    xaxis=dict(showspikes=True, spikemode="across", spikesnap="cursor", spikecolor="gray", spikethickness=1),
                )
                st.plotly_chart(fig, key="instrument_ohlc_chart")
            else:
                st.info("No price data available for this instrument.")

        st.stop()

# --- Download from Yahoo Finance --------------------------------------------------------------------------------------

st.divider()
st.subheader("Update prices data with yfinance")

message_container = st.empty()
progress_bar = st.progress(0, text="Idle")

with st.container(horizontal=True, horizontal_alignment="right"):
    btn_update_instruments = st.button(label="Download prices", type="primary")

if btn_update_instruments:
    
    with get_session() as session:

        orm_instruments = instruments_service.get_all(session)
        orm_ohlcvs = ohlcvs_service.get_latest_prices(session)

        step = math.floor(100 / len(orm_instruments)) if orm_instruments else 100
        progress = 0
        for instrument in orm_instruments:
            latest_ohlcv = OHLCV()
            latest_ohlcv.date = datetime.now() - timedelta(days=365)
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


# --- Load local JSON --------------------------------------------------------------------------------------------------

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
