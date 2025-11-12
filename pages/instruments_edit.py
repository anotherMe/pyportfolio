
import streamlit as st
from lib.database import get_session
from lib.models import Instrument
from lib.utils import is_valid_isin

from logging_config import setup_logger
log = setup_logger(__name__)

log.debug("Running instruments edit page...")

st.title("🔧 Instruments")

if 'instrument_id' not in st.session_state:
    st.session_state.instrument_id = None


with get_session() as session, session.begin():

    inst = None
    if st.session_state.instrument_id:
        st.subheader("Edit Instrument")
        inst = session.get(Instrument, st.session_state.instrument_id)
        if not inst:
            st.error("Instrument not found.")
            st.stop()
    else:
        st.subheader("Add new Instrument")
        inst = Instrument()

    with st.form("instrument_form"):

        inst.name = st.text_input("Name", value=inst.name or "")
        inst.name_long = st.text_input("Long name", value=inst.name_long or "")
        inst.description = st.text_area("Description", value=inst.description or "")
        inst.isin = st.text_input("ISIN", value=inst.isin or "")
        inst.ticker = st.text_input("Ticker", value=inst.ticker or "")
        inst.currency = st.text_input("Currency", value=inst.currency or "EUR")
        inst.category = st.selectbox(label="Category", options=["acc", "dist"], index=(0 if not inst.category else ["acc", "dist"].index(inst.category)))

        col1, col2 = st.columns([7,1])
        with col2:
            save = st.form_submit_button("💾 Save")
        if save:
            inst.isin = (inst.isin or "").strip().upper()
            if inst.isin and not is_valid_isin(inst.isin):
                st.warning("ISIN is invalid (bad format or checksum).")
            elif not inst.name:
                st.warning("Name cannot be empty.")
            else:
                session.add(inst)
                st.session_state.instrument_id = None
                st.success("✅ Instrument saved successfully!")
    
    col1, col2 = st.columns([5,1])
    with col2:
        if st.button("Back to list"):
            st.switch_page("pages/instruments_list.py")

