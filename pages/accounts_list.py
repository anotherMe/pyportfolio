
import logging
import streamlit as st
from lib.database import get_session
import lib.repo.accounts_repository as accounts_repo
from lib.utils import confirm_delete_dialog

from logging_config import setup_logger
log = setup_logger(__name__)

log.debug("Running accounts list page...")

def delete_account(item_id):
    with get_session() as session, session.begin():
        try:
            accounts_repo.delete_account(session, item_id)
            session.commit()
        except Exception:
            logging.exception("")
            st.error(f"Error while deleting item {item_id}")


st.title("🏦 Accounts")

with get_session() as session, session.begin():

    accounts = accounts_repo.get_all_accounts(session)

    if not accounts:
        st.info("No accounts found.")
        st.stop()

    # --- Search input ---
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
            with st.container(border=True):
                
                # --- Row 1: Name ---
                col1, col2 = st.columns([3,2])
                col1.markdown(f"**{acc.name}**: {acc.description}")

                col1, col2, col3 = st.columns([5,1,1])
                with col2:
                    if st.button("🗑️ Delete", key=f"delete_{acc.id}"):
                        confirm_delete_dialog(f"Are you sure you want to delete account {acc.name} ?", acc.id, delete_account)
                with col3:
                    if st.button("✏️ Edit", key=f"edit_{acc.id}"):
                        st.session_state["account_id"] = acc.id
                        st.switch_page("pages/accounts_edit.py")

    # --- Add new account button ---
        st.divider()
        col1, col2 = st.columns([4, 1])
        with col2:
            if st.button("➕ Add New"):
                st.session_state["account_id"] = None
                st.switch_page("pages/accounts_edit.py")