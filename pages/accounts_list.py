
from sqlalchemy import false, true
import streamlit as st

from lib.database import get_session
from lib.utils import confirm_delete_dialog
from service.accounts_service import AccountsService

from logging_config import setup_logger
log = setup_logger(__name__)

log.debug("Running accounts list page...")

accounts_service = AccountsService()


def delete_account(item_id):
    with get_session() as session:
        try:
            accounts_service.delete(session, item_id)
        except Exception:
            log.exception("")
            st.error(f"Error while deleting account {item_id}")


st.title("Accounts")

with get_session() as session:

    accounts = accounts_service.get_all(session)

    if not accounts:
        st.info("No accounts found.")
        st.stop()

    search_term = st.text_input("🔍 Search by Name or Description").strip().lower()
    if search_term:
        filtered_accounts = [
            acc for acc in accounts
            if search_term in (acc.name or "").lower()
            or search_term in (acc.description or "").lower()
        ]
    else:
        filtered_accounts = accounts

    if not filtered_accounts:
        st.info("No accounts found.")
    else:
        for acc in filtered_accounts:
            with st.container(horizontal=False, border=True):
                st.markdown(f"🏦 **{acc.name}**: {acc.description}")
                with st.container(horizontal=True, horizontal_alignment="right"):
                    if st.button("🗑️ Delete", key=f"delete_{acc.id}"):
                        confirm_delete_dialog(f"Are you sure you want to delete account {acc.name}?", acc.id, delete_account)
                    if st.button("✏️ Edit", key=f"edit_{acc.id}"):
                        st.session_state["account_id"] = acc.id
                        st.switch_page("pages/accounts_edit.py")

        st.divider()
        with st.container(horizontal=True, horizontal_alignment="right"):
            if st.button("➕ Add New"):
                st.session_state["account_id"] = None
                st.switch_page("pages/accounts_edit.py")
