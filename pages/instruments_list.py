
import streamlit as st
import pandas as pd

from lib.database import get_session
from lib.utils import confirm_delete_dialog
from service.instruments_service import InstrumentsService

from logging_config import setup_logger
log = setup_logger(__name__)

log.debug("Running instruments list page...")

if 'instrument_id' not in st.session_state:
    st.session_state.instrument_id = None

instruments_service = InstrumentsService()


def clear_search():
    st.session_state.instruments_list_search_term = ""


def delete_instrument(item_id):
    with get_session() as session:
        try:
            instruments_service.delete(session, item_id)
        except Exception:
            log.exception("")
            st.error(f"Error while deleting instrument {item_id}")


st.title("🔧 Instruments")
st.subheader("Instruments list")

with get_session() as session:
    instruments = instruments_service.get_all(session)

if not instruments:
    st.info("No instruments found.")
    st.stop()

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

if st_dataframe["selection"]["rows"]:
    dataframe_index = st_dataframe["selection"]["rows"][0]
    selected_instrument = filtered_instruments[dataframe_index]
    with st.container(horizontal=True):
        if st.button("Delete", type="primary"):
            confirm_delete_dialog(f"Are you sure you want to delete instrument {selected_instrument.id}?", selected_instrument.id, delete_instrument)
        if st.button("Edit", type="secondary"):
            st.session_state.instrument_id = selected_instrument.id
            st.switch_page("pages/instruments_edit.py")
        if st.button("Detail"):
            st.session_state.instrument_id = selected_instrument.id
            st.switch_page("pages/instruments_detail.py")
