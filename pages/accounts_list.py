
import streamlit as st
from lib.database import get_session
from lib.accounts_repository import get_all_accounts, delete_account

print("Running accounts list page...")

st.title("🏦 Accounts")

with get_session() as session, session.begin():

    accounts = get_all_accounts(session)

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
                        delete_account(session, acc.id)
                        st.success(f"Account '{acc.name}' deleted.")
                        st.rerun()
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