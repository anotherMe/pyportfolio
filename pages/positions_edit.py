
import streamlit as st

from lib.database import get_session
from service.accounts_service import AccountsService
from service.instruments_service import InstrumentsService
from service.positions_service import PositionsService
from service.dtos import PositionCreateDTO

from logging_config import setup_logger
log = setup_logger(__name__)

log.debug("Running Position edit page...")

st.title("Position")

if 'position_id' not in st.session_state:
    st.session_state.position_id = None
if 'instrument_id' not in st.session_state:
    st.session_state.instrument_id = None

accounts_service = AccountsService()
instruments_service = InstrumentsService()
positions_service = PositionsService()

with get_session() as session:

    accounts = accounts_service.get_all(session)
    accounts_map = {acc.name: acc for acc in accounts}
    instruments = instruments_service.get_all(session)
    instrument_map = {inst.name: inst for inst in instruments}

    is_editing = bool(st.session_state.position_id)

    if is_editing:
        positions = positions_service.get_all_basic(session)
        position = next((p for p in positions if p.id == st.session_state.position_id), None)
        if position is None:
            st.error("Position not found.")
            st.stop()
        with st.container(horizontal=True):
            st.subheader(f"Editing Position with ID: {position.id}")
            if st.button("Clear selection"):
                st.session_state.position_id = None
                st.session_state.instrument_id = None
                st.rerun()
    else:
        st.subheader("Add new Position")
        position = None

    with st.form("position_form"):

        # Pre-select instrument if coming from instruments page
        selected_instrument_index = None
        if st.session_state.instrument_id:
            target = next((inst for inst in instruments if inst.id == st.session_state.instrument_id), None)
            if target:
                selected_instrument_index = list(instrument_map.keys()).index(target.name)

        # Pre-select account/instrument when editing
        account_index = 0
        if is_editing and position:
            if position.account_name in accounts_map:
                account_index = list(accounts_map.keys()).index(position.account_name)
            if position.instrument_name in instrument_map:
                selected_instrument_index = list(instrument_map.keys()).index(position.instrument_name)

        selected_account = st.selectbox("Account", list(accounts_map.keys()), index=account_index)
        selected_instrument = st.selectbox("Instrument", list(instrument_map.keys()), index=selected_instrument_index)

        col1, col2 = st.columns([7, 1])
        with col2:
            save = st.form_submit_button("💾 Save")

        if save:
            if not selected_instrument:
                st.warning("Instrument must be selected.")
            else:
                try:
                    account_id = accounts_map[selected_account].id
                    instrument_id = instrument_map[selected_instrument].id
                    if is_editing and position:
                        # Update: patch the model directly
                        from lib.models import Position as PositionModel
                        model = session.get(PositionModel, position.id)
                        model.account_id = account_id
                        model.instrument_id = instrument_id
                        session.commit()
                    else:
                        dto = PositionCreateDTO(account_id=account_id, instrument_id=instrument_id)
                        positions_service.create(session, dto)
                    st.session_state.position_id = None
                    st.session_state.instrument_id = instrument_id
                    st.success("✅ Position saved successfully!")
                except Exception as e:
                    log.exception("")
                    st.error(f"Error saving position: {e}")

    with st.container(horizontal=True):
        st.space("stretch")
        if st.button("Back to list"):
            st.switch_page("pages/positions_list.py")
