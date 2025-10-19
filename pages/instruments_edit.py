
import streamlit as st
from lib import accounts_repository
from lib.database import get_session
from lib.models import Instrument
from lib.streamlit.account_selector import extract_current_account_from_params
from lib.utils import is_valid_isin


print("Running instruments edit page...")

st.title("🔧 Instruments")

if 'instrument_id' not in st.session_state:
    st.session_state.instrument_id = None


with get_session() as session, session.begin():
    
    currenct_account = extract_current_account_from_params(session)

    accounts = accounts_repository.get_all_accounts(session)
    account_options = [account.name for account in accounts]

    if st.session_state.instrument_id:

        st.subheader("Edit Instrument")

        inst = session.get(Instrument, st.session_state.instrument_id)
        if not inst:
            st.error("Instrument not found.")
        else:
            
            with st.form("instrument_form"):
                selected_account_name = st.selectbox("Select Account", options=account_options, index=0)
                inst.account_id = next(
                    (account.id for account in accounts if account.name == selected_account_name),
                    None
                )
                inst.isin = st.text_input("ISIN", value=inst.isin or "")
                inst.ticker = st.text_input("Ticker", value=inst.ticker or "")
                inst.name = st.text_input("Name", value=inst.name or "")
                inst.currency = st.text_input("Currency", value=inst.currency or "EUR")
                save = st.form_submit_button("💾 Save")

                if save:
                    if not inst.isin:
                        st.warning("ISIN cannot be empty.")
                    elif not inst.name:
                        st.warning("Name cannot be empty.")
                    else:
                        session.add(inst)
                        st.success("✅ Instrument saved successfully!")

    else:

        st.subheader("Add New Instrument")
        
        with st.form("instrument_form"):

            inst = Instrument()
            selected_account_name = st.selectbox("Account", options=account_options, index=0)
            inst.account_id = next(
                (account.id for account in accounts if account.name == selected_account_name),
                None
            )
            inst.isin = st.text_input("ISIN", value=inst.isin or "")
            inst.ticker = st.text_input("Ticker", value=inst.ticker or "")
            inst.name = st.text_input("Name", value=inst.name or "")
            inst.currency = st.text_input("Currency", value=inst.currency or "EUR")

            col1, col2 = st.columns([7,1])
            with col2:
                save = st.form_submit_button("💾 Save")

            if save:
                inst.isin = (inst.isin or "").strip().upper()
                if not inst.isin:
                    st.warning("ISIN cannot be empty.")
                elif not is_valid_isin(inst.isin):
                    st.warning("ISIN is invalid (bad format or checksum).")
                    st.stop()
                elif not inst.name:
                    st.warning("Name cannot be empty.")
                else:
                    session.add(inst)
                    st.session_state.instrument_id = None
                    st.success("✅ Instrument saved successfully!")
    
    col1, col2 = st.columns([5,1])
    with col2:
        if st.button("Back to details"):
            st.switch_page("pages/instruments_details.py")

