
import streamlit as st

from lib.database import get_session
from service.accounts_service import AccountsService
from service.dtos import AccountCreateDTO

from logging_config import setup_logger
log = setup_logger(__name__)

log.debug("Running accounts edit page...")

if 'account_id' not in st.session_state:
    st.session_state.account_id = None

st.title("🔧 Accounts")

accounts_service = AccountsService()

with get_session() as session:

    if st.session_state.account_id:

        accounts = accounts_service.get_all(session)
        account = next((a for a in accounts if a.id == st.session_state.account_id), None)

        if account is None:
            st.error("Account not found.")
            st.stop()

        with st.container(horizontal=True):
            st.subheader(f"Editing Account with ID: {st.session_state.account_id}")
            if st.button("Clear selection"):
                st.session_state.account_id = None
                st.rerun()

        with st.form("account_form"):
            name = st.text_input("Name", value=account.name or "")
            description = st.text_input("Description", value=account.description or "")
            save = st.form_submit_button("💾 Save")

            if save:
                if not name:
                    st.warning("Name cannot be empty.")
                else:
                    try:
                        # Use repo directly for update (no update service method needed for simple case)
                        from lib.models import Account as AccountModel
                        model = session.get(AccountModel, account.id)
                        model.name = name
                        model.description = description
                        session.commit()
                        st.success("✅ Account saved successfully!")
                    except Exception as e:
                        log.exception("")
                        st.error(f"Error saving account: {e}")

    else:

        st.subheader("Add New Account")

        with st.form("account_form"):
            name = st.text_input("Name")
            description = st.text_input("Description")

            col1, col2 = st.columns([7, 1])
            with col2:
                save = st.form_submit_button("💾 Save")

            if save:
                if not name:
                    st.warning("Name cannot be empty.")
                else:
                    try:
                        accounts_service.create(session, AccountCreateDTO(name=name, description=description or None))
                        st.session_state.account_id = None
                        st.success("✅ Account saved successfully!")
                    except Exception as e:
                        log.exception("")
                        st.error(f"Error saving account: {e}")

    col1, col2 = st.columns([5, 1])
    with col2:
        if st.button("Back to list"):
            st.switch_page("pages/accounts_list.py")
