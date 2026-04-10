
import streamlit as st

from lib.database import get_session
from lib.enums import Currency, DistributionPolicy
from lib.utils import is_valid_isin
from service.instruments_service import InstrumentsService
from service.dtos import InstrumentCreateDTO

from logging_config import setup_logger
log = setup_logger(__name__)

log.debug("Running instruments edit page...")

st.title("🔧 Instruments")

if 'instrument_id' not in st.session_state:
    st.session_state.instrument_id = None

instruments_service = InstrumentsService()

with get_session() as session:

    inst_dto = None
    if st.session_state.instrument_id:
        instruments = instruments_service.get_all(session)
        inst_dto = next((i for i in instruments if i.id == st.session_state.instrument_id), None)

        if inst_dto is None:
            st.error("Instrument not found.")
            st.stop()

        with st.container(horizontal=True):
            st.subheader(f"Editing Instrument with ID: {inst_dto.id}")
            if st.button("Clear selection"):
                st.session_state.instrument_id = None
                st.rerun()
    else:
        st.subheader("Add new Instrument")

    with st.form("instrument_form"):

        name = st.text_input("Name", value=inst_dto.name if inst_dto else "")
        name_long = st.text_input("Long name", value=inst_dto.name_long if inst_dto else "")
        description = st.text_area("Description", value=inst_dto.description if inst_dto else "")
        isin = st.text_input("ISIN", value=inst_dto.isin if inst_dto else "")
        ticker = st.text_input("Ticker", value=inst_dto.ticker if inst_dto else "")

        currency_options = list(Currency)
        current_currency = inst_dto.currency if inst_dto else Currency.EUR
        currency_index = currency_options.index(current_currency)
        selected_currency = st.selectbox(
            "Currency",
            options=currency_options,
            format_func=lambda c: f"{c.name} – {c.full_name} ({c.symbol})",
            index=currency_index,
        )

        dist_policy_options = list(DistributionPolicy)
        dist_policy_labels = {c: c.value for c in dist_policy_options}
        current_dist_policy = inst_dto.dist_policy if inst_dto else DistributionPolicy.ACCUMULATING
        dist_policy_index = dist_policy_options.index(current_dist_policy) if current_dist_policy in dist_policy_options else 0
        selected_dist_policy = st.selectbox(
            "Distribution policy",
            options=dist_policy_options,
            format_func=lambda c: c.value,
            index=dist_policy_index,
        )

        col1, col2 = st.columns([7, 1])
        with col2:
            save = st.form_submit_button("💾 Save")

        if save:
            clean_isin = (isin or "").strip().upper()
            if clean_isin and not is_valid_isin(clean_isin):
                st.warning("ISIN is invalid (bad format or checksum).")
            elif not name:
                st.warning("Name cannot be empty.")
            else:
                try:
                    if inst_dto:
                        # Update: load model and patch directly
                        from lib.models import Instrument as InstrumentModel
                        model = session.get(InstrumentModel, inst_dto.id)
                        model.name = name
                        model.name_long = name_long or None
                        model.description = description or None
                        model.isin = clean_isin or None
                        model.ticker = ticker or None
                        model.currency = selected_currency
                        model.dist_policy = selected_dist_policy
                        session.commit()
                    else:
                        instruments_service.create(session, InstrumentCreateDTO(
                            name=name,
                            currency=selected_currency,
                            isin=clean_isin or None,
                            ticker=ticker or None,
                            name_long=name_long or None,
                            dist_policy=selected_dist_policy,
                            description=description or None,
                        ))
                    st.session_state.instrument_id = None
                    st.success("✅ Instrument saved successfully!")
                except Exception as e:
                    log.exception("")
                    st.error(f"Error saving instrument: {e}")

    with st.container(horizontal=True):
        st.space("stretch")
        if st.button("Back to list"):
            st.switch_page("pages/instruments_list.py")
