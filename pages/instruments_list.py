
import streamlit as st
from lib.database import get_session
from lib.models import Instrument
import lib.repo.instruments_repository as instruments_repo
import pandas as pd

from lib.utils import confirm_delete_dialog

from logging_config import setup_logger
log = setup_logger(__name__)

log.debug("Running instruments list page...")


if 'instrument_id' not in st.session_state:
    st.session_state.instrument_id = None

def clear_search():
    st.session_state.search_term = ""

def delete_instrument(item_id):
    with get_session() as session, session.begin():
        try:
            instruments_repo.delete_instrument(session, item_id)
            session.commit()
        except Exception:
            log.exception("")
            st.err

st.title("🔧 Instruments")
st.subheader("Instruments list")

with get_session() as session:
    instruments = instruments_repo.get_all_instruments(session)

if not instruments:
    st.info("No instruments found.")
    st.stop()

# --- Search input ---
col1, col2 = st.columns([5, 1], vertical_alignment="bottom")
with col1:
    # st.space("stretch")
    search_term = st.text_input("🔍 Search by Instrument ISIN, Ticker, or Name", key="search_term" ).strip().lower()
with col2:
    st.button(label="", icon=":material/clear_all:", on_click=clear_search)

        
if search_term:
    st.session_state.instruments_list_search_term = search_term
    filtered_instruments = [
        instrument for instrument in instruments
        if search_term in (instrument.isin or "").lower()
        or search_term in (instrument.ticker or "").lower()
        or search_term in (instrument.name or "").lower()
    ]
else:
    filtered_instruments = instruments
    

if not filtered_instruments:
    st.info("No Instruments corresponding to the current search")
    st.stop()


# --- Create dataframe ---
data = []
for inst in filtered_instruments:
    data.append({
        # "ID": inst.id,
        "ISIN": f"https://www.justetf.com/en/etf-profile.html?isin={inst.isin}" if inst.isin else "",
        "Ticker": f"https://finance.yahoo.com/quote/{inst.ticker}" if inst.ticker else "",
        "Name": inst.name,
        # "Currency": inst.currency or "",
    })

df = pd.DataFrame(data)

# --- Configure columns ---
column_config = {
    "ISIN": st.column_config.LinkColumn(
        help="Look up ISIN on JustETF site",
        display_text=r"[?&]isin=([^&#]+)"
    ),
    "Ticker": st.column_config.LinkColumn(
        help="Lookup ticker on Yahoo Finance site",
        display_text=r"/quote/([^/?#]+)"
    ),
}

# --- Display table ---
st_dataframe = st.dataframe(
    data=df,
    hide_index=True,
    column_config=column_config,
    on_select="rerun",
    selection_mode="single-row"
)

# --- If a row has been selected, show buttons
if st_dataframe["selection"]["rows"]:
    dataframe_index = st_dataframe["selection"]["rows"][0]
    selected_instrument: Instrument = filtered_instruments[dataframe_index]
    with st.container(horizontal=True):
        # st.space("stretch")
        if st.button("Detail"):
            st.session_state.instrument_id = selected_instrument.id
            st.switch_page("pages/instruments_detail.py")
        if st.button("Edit", type="secondary"):
            st.session_state.instrument_id = selected_instrument.id
            st.switch_page("pages/instruments_edit.py")
        if st.button("Delete", type="primary"):
            confirm_delete_dialog(f"Are you sure you want to delete trade {selected_instrument.id} ?", 
                                  selected_instrument.id, delete_instrument)