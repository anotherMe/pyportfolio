
import streamlit as st
from lib.database import get_session
from lib.instruments_repository import get_all_instruments
import pandas as pd


print("Running instruments list page...")

st.session_state.instrument_id = None  # Always reset selected instrument ID


st.title("🔧 Instruments")
st.subheader("Instruments list")

with get_session() as session, session.begin():
        
    instruments = get_all_instruments(session)

    if not instruments:
        st.info("No instruments found.")
        st.stop()

    for inst in instruments:
        cols = st.columns([3,2,10,2], border=False)
        cols[0].write(inst.isin)
        cols[1].write(inst.ticker)
        cols[2].write(inst.name)
        if cols[3].button("Edit", key=f"edit_{inst.id}"):
            # set the query param (string values)
            # TODO: set current instrument_id in the st.session_state
            # then programmatically switch page (no new tab)
            st.switch_page("pages/instruments_edit.py")
