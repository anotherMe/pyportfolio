
import logging
import streamlit as st
from lib.repo.accounts_repository import get_account_by_name, get_all_accounts
from lib.database import read_from_db, get_session
from service.utils import account_selector, to_local
import lib.repo.transactions_repository as trans_repo

st.session_state.transaction_id = None  # Always reset selected transaction ID


@st.dialog("Confirm transaction deletion")
def confirm_delete_dialog(item, on_confirm):
    st.write(f"Are you sure you want to delete transaction {item} ?")
    col1, col2, col3 = st.columns([3,1,1])
    with col2:
        if st.button("✅ Yes"):
            on_confirm()
            st.rerun()
    with col3:
        if st.button("❌ No"):
            st.rerun()

def delete_transaction(item_id):
    with get_session() as session, session.begin():
        try:
            trans_repo.delete_transaction(session, item_id)
            st.success("Transaction deleted successfully")
        except Exception:
            logging.exception()
            st.error("Error deleting transaction")


st.title("💰 Transactions")
st.subheader("Transaction Details")

with get_session() as session, session.begin():

    accounts = get_all_accounts(session)
    account_selector(accounts) # Show sidebar account selector
    current_account = get_account_by_name(session, st.session_state.account)
    transactions = trans_repo.get_all_transactions(session, current_account)


    if not transactions:
        st.info("No transactions found.")
        st.stop()

    # --- Search filters ---
    search_term = st.text_input("🔍 Search by Instrument (ISIN, Ticker, Name) or by Transaction description").strip().lower()

    if search_term:
        filtered_transactions = [
            trans for trans in transactions
            if ( trans.trade and
                ( search_term in (trans.trade.instrument.isin or "").lower()
                or search_term in (trans.trade.instrument.ticker or "").lower()
                or search_term in (trans.trade.instrument.name or "").lower() ) ) 
            or ( not trans.trade and search_term in (trans.description or "").lower())
        ]
    else:
        filtered_transactions = []

    start_date = st.date_input("Start Date", value=None, key="start_date_filter")
    end_date = st.date_input("End Date", value=None, key="end_date_filter")
    if start_date or end_date:
        def in_filter_range(transaction):
            if start_date and transaction.date.date() < start_date:
                return False
            if end_date and transaction.date.date() > end_date:
                return False
            return True

        filtered_transactions = [
            transaction for transaction in filtered_transactions
            if in_filter_range(transaction)
        ]
    else:
        filtered_transactions = filtered_transactions

    if not filtered_transactions:
        st.info("No transactions found for the current search")
        st.stop()

    # --- Transaction list ---
    for trans in filtered_transactions:
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
                    confirm_delete_dialog(trans.id, lambda: delete_transaction(trans.id))
            with col3:
                if st.button("✏️ Edit", key=f"edit_{trans.id}"):
                    st.session_state["transaction_id"] = trans.id
                    st.switch_page("pages/transactions_edit.py")
