
import streamlit as st
from lib.accounts_repository import get_account_by_name, get_all_accounts
from lib.database import read_from_db, get_session
from lib.streamlit.utils import account_selector
import lib.transactions_repository as trans_repo


print("Running transactions details page...")

st.session_state.transaction_id = None  # Always reset selected transaction ID
if "ok_delete_transaction" not in st.session_state:
    st.session_state.ok_delete_transaction = False
if "show_delete_transaction_confirmation_dialog" not in st.session_state:
    st.session_state.show_delete_transaction_confirmation_dialog = False

st.title("💰 Transactions")
st.subheader("Transaction Details")

@st.dialog("Confirm transaction deletion")
def confirm_delete_dialog():
    st.write("Are you sure you want to delete this transaction ?")
    col1, col2, col3 = st.columns([3,1,1])
    with col2:
        if st.button("✅ Yes"):
            st.session_state.ok_delete_transaction = True
            st.rerun()
    with col3:
        if st.button("❌ No"):
            st.session_state.show_delete_transaction_confirmation_dialog = False
            st.rerun()

with get_session() as session, session.begin():

    # --- Account selector ---
    accounts = get_all_accounts(session)
    account_selector(accounts) # Show sidebar account selector
    current_account = get_account_by_name(session, st.session_state.account)

    transactions = trans_repo.get_all_transactions(session, current_account)

    if not transactions:
        st.info("No transactions found.")
        st.stop()

    # Search filter by date range
    start_date = st.date_input("Start Date", value=None, key="start_date_filter")
    end_date = st.date_input("End Date", value=None, key="end_date_filter")
    if start_date or end_date:
        def in_date_range(transaction):
            if start_date and transaction.date.date() < start_date:
                return False
            if end_date and transaction.date.date() > end_date:
                return False
            return True

        filtered_transactions = [
            transaction for transaction in transactions
            if in_date_range(transaction)
        ]

    else:
        filtered_transactions = transactions

    if not filtered_transactions:
        st.info("No transactions found.")
    else:
        for trans in filtered_transactions:
            with st.container(border=True):
                
                # --- Row 1 ---
                if trans.description:
                    st.subheader(trans.description)

                # --- Row 2 ---
                col1, col2 = st.columns([2, 1])
                col1.markdown(f"**Instrument:** {trans.trade.instrument.name}")
                col2.markdown(f"**Type:** {trans.type}")
                
                # --- Row 3 ---
                col1, col2 = st.columns([2, 1])
                col1.markdown(f"**Date:** {trans.date.strftime('%Y-%m-%d %H:%M')}")
                col2.markdown(f"**Amount (€):** {read_from_db(trans.amount)}")

                # --- Row 4: Button bar ---
                col1, col2, col3 = st.columns([6, 1, 1])  # last column small for button
                with col2:

                    if not st.session_state.ok_delete_transaction:
                        if st.button("🗑️ Delete", key=f"delete_{trans.id}"):
                            st.session_state.show_delete_transaction_confirmation_dialog = True
                            st.rerun()
                    else:
                        try:
                            trans_repo.delete_transaction(session, trans.id)
                            st.success("Transaction deleted successfully")
                            st.session_state.ok_delete_transaction = False  # VERY IMPORTANT: without this, it would keep deleting ALL transactions
                            st.session_state.show_delete_transaction_confirmation_dialog = False
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error deleting transaction: {e}")

                    if st.session_state.show_delete_transaction_confirmation_dialog:
                        confirm_delete_dialog()

                with col3:
                    if st.button("✏️ Edit", key=f"edit_{trans.id}"):
                        st.session_state["transaction_id"] = trans.id
                        st.switch_page("pages/transactions_edit.py")
