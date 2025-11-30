
import logging
import streamlit as st
from lib.models import Transaction
from lib.repo.accounts_repository import get_account_by_name, get_all_accounts
from lib.database import read_from_db, get_session
from lib.utils import confirm_delete_dialog
from service.utils import account_selector, to_local
import lib.repo.transactions_repository as trans_repo

print("Running transactions details page...")

if "transaction_id" not in st.session_state:
    st.session_state.transaction_id = None


def delete_transaction(item_id):
    with get_session() as session, session.begin():
        try:
            trans_repo.delete_transaction(session, item_id)
            session.commit()
        except Exception:
            logging.exception("")
            st.error(f"Error while deleting item {item_id}")


st.title("💰 Transactions")
st.subheader("Transaction Details")

if not st.session_state.transaction_id:
    st.write("No Transaction selected")
    if st.button("Back to list"):
        st.switch_page("pages/transactions_list.py")
    st.stop()

with get_session() as session, session.begin():

    accounts = get_all_accounts(session)
    account_selector(accounts) # Show sidebar account selector
    current_account = get_account_by_name(session, st.session_state.account)

    trans = session.get(Transaction, st.session_state.transaction_id)

    with st.container(border=True):
        
        # --- Row 1 ---
        if trans.description:
            st.subheader(trans.description)

        # --- Row 2 ---
        col1, col2 = st.columns([2, 1])
        if trans.trade:
            col1.markdown(f"**Instrument:** {trans.trade.instrument.name}")
        col2.markdown(f"**Type:** {trans.type}")
        
        # --- Row 3 ---
        col1, col2 = st.columns([2, 1])
        col1.markdown(f"**Date:** {to_local(trans.date)}")
        col2.markdown(f"**Amount (€):** {read_from_db(trans.amount)}")

        # --- Row 4: Button bar ---
        col1, col2, col3 = st.columns([6, 1, 1])  # last column small for button
        with col2:
            if st.button("🗑️ Delete", key=f"delete_{trans.id}"):
                confirm_delete_dialog(f"Are you sure you want to delete transaction {trans.id} ?", trans.id, delete_transaction)
        with col3:
            if st.button("✏️ Edit", key=f"edit_{trans.id}"):
                st.session_state["transaction_id"] = trans.id
                st.switch_page("pages/transactions_edit.py")
