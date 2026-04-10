
import streamlit as st

from lib.database import get_session
from lib.utils import confirm_delete_dialog
from service.instruments_service import InstrumentsService

from logging_config import setup_logger
log = setup_logger(__name__)

log.debug("Running instruments details page...")

if "instrument_id" not in st.session_state:
    st.session_state.instrument_id = None

instruments_service = InstrumentsService()


def delete_instrument(item_id):
    with get_session() as session:
        try:
            instruments_service.delete(session, item_id)
            st.switch_page("pages/instruments_list.py")
        except Exception:
            log.exception("")
            st.error(f"Error while deleting instrument {item_id}")


st.title("🔧 Instruments")
st.subheader("Instrument Details")

if not st.session_state.instrument_id:
    st.write("No Instrument selected")
    if st.button("Back to list"):
        st.switch_page("pages/instruments_list.py")
    st.stop()

with get_session() as session:

    instruments = instruments_service.get_all(session)
    inst = next((i for i in instruments if i.id == st.session_state.instrument_id), None)

    if inst is None:
        st.error("Instrument not found.")
        st.stop()

    with st.container(border=True):

        st.subheader(inst.name)

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

        st.write(" ")

        col1, col2, col3 = st.columns([6, 1, 1])
        with col2:
            if st.button("✏️ Edit", key=f"edit_{inst.id}"):
                st.session_state["instrument_id"] = inst.id
                st.switch_page("pages/instruments_edit.py")
        with col3:
            if st.button("🗑️ Delete", key=f"delete_{inst.id}"):
                confirm_delete_dialog(f"Are you sure you want to delete instrument {inst.id}?", inst.id, delete_instrument)

    with st.container(horizontal=True):
        st.space("stretch")
        if st.button("Back to list"):
            st.switch_page("pages/instruments_list.py")
