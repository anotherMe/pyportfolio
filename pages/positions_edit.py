
import streamlit as st
from lib.database import get_session
from lib.models import Instrument, Position
from lib.repo.accounts_repository import get_all_accounts
from lib.repo.instruments_repository import get_all_instruments

from logging_config import setup_logger
log = setup_logger(__name__)

log.debug("Running Position edit page...")

st.title("Position")

if 'position_id' not in st.session_state:
    st.session_state.position_id = None
if 'instrument_id' not in st.session_state:
    st.session_state.instrument_id = None

with get_session() as session, session.begin():

    position = None
    if st.session_state.position_id:
        position = session.get(Position, st.session_state.position_id)
        with st.container(horizontal=True):
            st.subheader(f"Editing Position with ID: {position.id}")
            if st.button("Clear selection"):
                st.session_state.position_id = None
                st.session_state.instrument_id = None
                st.rerun()
        if not position:
            st.error("Position not found.")
            st.stop()
    else:
        st.subheader("Add new Position")
        position = Position()
        position.closed = False

    accounts = get_all_accounts(session)
    accounts_map = {account.name: account for account in accounts}
    instruments = get_all_instruments(session)
    instrument_map = {inst.name: inst for inst in instruments}

    with st.form("position_form"):

        # if an instrument has been set from instrument_detail.py
        selected_instrument_index = None
        if st.session_state.instrument_id:
            work_on_instrument = session.get(Instrument, st.session_state.instrument_id)
            selected_instrument_index = list(instrument_map.keys()).index(work_on_instrument.name)

        selected_account = st.selectbox(
            "Account",
            list(accounts_map.keys())
        )
        selected_instrument = st.selectbox(
            "Instrument",
            list(instrument_map.keys()),
            index=selected_instrument_index
        )

        col1, col2 = st.columns([7,1])
        with col2:
            save = st.form_submit_button("💾 Save")
        if save:
            if not selected_instrument:
                st.warning("Instrument must be selected.")
            else:
                instrument_id = instrument_map.get(selected_instrument).id
                position.account_id = accounts_map.get(selected_account).id
                position.instrument_id = instrument_id
                session.add(position)
                st.session_state.position_id = None
                st.session_state.instrument_id = instrument_id
                st.success("✅ Position saved successfully!")
    
    with st.container(horizontal=True):
        st.space("stretch")
        if st.button("Back to list"):
            st.switch_page("pages/positions_list.py")

