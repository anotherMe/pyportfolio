
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from lib.database import get_session
from lib.utils import confirm_delete_dialog
from service.instruments_service import InstrumentsService
from service.ohlcvs_service import OhlcvsService

from logging_config import setup_logger
log = setup_logger(__name__)

log.debug("Running instruments list page...")

if 'instrument_id' not in st.session_state:
    st.session_state.instrument_id = None

instruments_service = InstrumentsService()
ohlcvs_service = OhlcvsService()


# ----------------------------------------------------------------------------------------------------------------------
# utility functions 

def clear_search():
    st.session_state.instruments_list_search_term = ""


def delete_instrument(item_id):
    with get_session() as session:
        try:
            instruments_service.delete(session, item_id)
        except Exception:
            log.exception("")
            st.error(f"Error while deleting instrument {item_id}")


# ----------------------------------------------------------------------------------------------------------------------
# page layout

st.title("🔧 Instruments")
st.subheader("Instruments list")

with get_session() as session:
    instruments = instruments_service.get_all(session)

if not instruments:
    st.info("No instruments found.")
    st.stop()

# ----------------------------------------------------------------------------------------------------------------------
# instruments filter

col1, col2 = st.columns([5, 1], vertical_alignment="bottom")
with col1:
    search_term = st.text_input("🔍 Search by Instrument ISIN, Ticker, or Name", key="search_term").strip().lower()
with col2:
    st.button(label="", icon=":material/clear_all:", on_click=clear_search)

if search_term:
    filtered_instruments = [
        inst for inst in instruments
        if search_term in (inst.isin or "").lower()
        or search_term in (inst.ticker or "").lower()
        or search_term in (inst.name or "").lower()
    ]
else:
    filtered_instruments = instruments

if not filtered_instruments:
    st.info("No Instruments corresponding to the current search")
    st.stop()

# ----------------------------------------------------------------------------------------------------------------------
# data frame

data = []
for inst in filtered_instruments:
    data.append({
        "inst_id": inst.id,
        "Name": inst.name,
        "ISIN": f"https://www.justetf.com/en/etf-profile.html?isin={inst.isin}" if inst.isin else "",
        "Ticker": f"https://finance.yahoo.com/quote/{inst.ticker}" if inst.ticker else "",
        "Currency": inst.currency.name if inst.currency else "",
        "Dist. policy": inst.dist_policy.value if inst.dist_policy else "",
    })

df = pd.DataFrame(data)

column_config = {
    "inst_id": None,
    "ISIN": st.column_config.LinkColumn(
        help="Look up ISIN on JustETF site",
        display_text=r"[?&]isin=([^&#]+)",
    ),
    "Ticker": st.column_config.LinkColumn(
        help="Lookup ticker on Yahoo Finance site",
        display_text=r"/quote/([^/?#]+)",
    ),
}

st_dataframe = st.dataframe(
    data=df,
    hide_index=True,
    column_config=column_config,
    on_select="rerun",
    selection_mode="single-row",
)

with st.container(horizontal=True, horizontal_alignment="right"):
    if st.button("➕ Add new", type="secondary"):
        st.session_state["instrument_id"] = None
        st.switch_page("pages/instruments_edit.py")

st.space()

# ----------------------------------------------------------------------------------------------------------------------
# manage instrument selection

selected_rows = st_dataframe.selection.rows  # type: ignore[union-attr]
if selected_rows:
    selected_id = df.iloc[selected_rows[0]]["inst_id"]
    inst = next(i for i in filtered_instruments if i.id == selected_id)
    selected_instrument = inst

    # ----------------------------------------------------------------------------------------------------------------------
    # instrument details

    with st.container(border=True):
        st.subheader(inst.name)
        st.write(f"ID: {inst.id}")
        if inst.name_long:
            st.markdown(f"**{inst.name_long.strip()}**")
        col1, col2, col3 = st.columns([2, 1, 3])
        if inst.isin:
            col1.write(f"**ISIN:** [{inst.isin}](https://www.justetf.com/en/etf-profile.html?isin={inst.isin})")
        if inst.ticker:
            col2.markdown(f"**Ticker**: [{inst.ticker}](https://finance.yahoo.com/quote/{inst.ticker})")
        col1, col2, col3 = st.columns([2, 1, 3])
        if inst.currency:
            col1.write(f"**Currency:** {inst.currency.name} ({inst.currency.symbol})")
        if inst.dist_policy:
            col2.markdown(f"**Dist. policy**: {inst.dist_policy.value}")
        if inst.description:
            st.write(inst.description)

        # --------------------------------------------------------------------------------------------------------------
        # buttons

        with st.container(horizontal=True, horizontal_alignment="right"):
            if st.button("Delete", type="primary"):
                confirm_delete_dialog(f"Are you sure you want to delete instrument {selected_instrument.id}?", selected_instrument.id, delete_instrument)
            if st.button("Edit", type="secondary"):
                st.session_state.instrument_id = selected_instrument.id
                st.switch_page("pages/instruments_edit.py")


# --------------------------------------------------------------------------------------------------------------
# price chart

    st.space()
    with st.container(border=True):
        with get_session() as session:
            prices_list = ohlcvs_service.get_prices_for_instrument(session, inst.id)

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
                title=f"{inst.name} — Price History",
                xaxis_title="Date",
                yaxis_title="Price",
                height=800,
                hovermode="x unified",
                xaxis=dict(showspikes=True, spikemode="across", spikesnap="cursor", spikecolor="gray", spikethickness=1),
            )
            st.plotly_chart(fig, key="instrument_ohlc_chart")
        else:
            st.info("No price data available for this instrument.")

