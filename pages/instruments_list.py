
import streamlit as st
from lib.database import get_session
from lib.models import Instrument
import lib.repo.instruments_repository as instruments_repo
import pandas as pd

from lib.utils import confirm_delete_dialog

from logging_config import setup_logger
log = setup_logger(__name__)

log.debug("Running instruments list page...")

st.session_state.instrument_id = None  # Always reset selected instrument ID

def delete_instrument(item_id):
    with get_session() as session, session.begin():
        try:
            instruments_repo.delete_instrument(session, item_id)
            session.commit()
        except Exception:
            log.exception("")
            st.error(f"Error while deleting item {item_id}")


st.title("🔧 Instruments")
st.subheader("Instruments list")

with get_session() as session:
    instruments = instruments_repo.get_all_instruments(session)

if not instruments:
    st.info("No instruments found.")
    st.stop()

# --- Create dataframe ---
data = []
for inst in instruments:
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

if st_dataframe["selection"]["rows"]:
    dataframe_index = st_dataframe["selection"]["rows"][0]
    selected_instrument: Instrument = instruments[dataframe_index]
    with st.container(horizontal=True):
        # st.space("stretch")
        if st.button("Show details"):
            st.session_state.instrument_id = selected_instrument.id
            st.switch_page("pages/instruments_edit.py")
        if st.button("Delete", type="primary"):
            confirm_delete_dialog(f"Are you sure you want to delete trade {selected_instrument.id} ?", 
                                  selected_instrument.id, delete_instrument)