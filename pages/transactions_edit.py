

from datetime import datetime
import streamlit as st
from lib.repo.accounts_repository import get_all_accounts
from lib.database import read_from_db, get_session, write_to_db
from lib.models import Transaction
from lib.models import Trade
from lib.settings_manager import get_timezone


print("Running transactions edit page...")

if 'transaction_id' not in st.session_state:
    st.session_state.transaction_id = None

if 'trade_id' not in st.session_state:
    st.session_state.trade_id = None


st.title("💰 Transactions")

with get_session() as session, session.begin():

    accounts = get_all_accounts(session)
    accounts_map = {account.name: account for account in accounts}

    if st.session_state.transaction_id:

        st.subheader("Edit Transaction")

        transaction = session.get(Transaction, st.session_state.transaction_id)
        if not transaction:
            st.error("Transaction not found.")
        else:
            
            # --- Transaction form ---
            with st.form("dividend_form"):
                selected_account = st.selectbox(
                    "Account",
                    list(accounts_map.keys()),
                    index=list(accounts_map.keys()).index(transaction.account.name), 
                )
                transaction_type = st.selectbox(
                    "Transaction Type",
                    options=["div", "tax", "fee"],
                    index=["div", "tax", "fee"].index(transaction.type),
                    disabled=False
                )
                transaction_date = st.date_input("Transaction date", value=transaction.date)
                transaction_time = st.time_input("Transaction time", value=transaction.date.time(), step=60)
                amount = st.number_input("Amount (€)", min_value=0.0, step=0.01, value=read_from_db(transaction.amount))
                submitted = st.form_submit_button("Save Transaction")

                if submitted:
                    # TODO: add validation
                    transaction.account = accounts_map.get(selected_account)
                    transaction.type = transaction_type
                    transaction.date = datetime.combine(transaction_date, transaction_time).replace(tzinfo=get_timezone())
                    transaction.amount = write_to_db(amount)
                    session.add(transaction)
                    st.success(f"Transaction for {transaction.id} updated successfully!")

    else:

        st.subheader("Add new transaction")

        # --- Manage default values if session_state contains trade_id
        t = None
        selected_account_index = 0
        transaction_date_default = datetime.now()
        transaction_time_default = transaction_date_default.time()
        if st.session_state.trade_id:  # trade ID coming from page trades_details.py
            t = session.get(Trade, st.session_state.trade_id)
            selected_account_index = list(accounts_map.keys()).index(t.account.name)
            transaction_date_default = t.date.date()
            transaction_time_default = t.date.time()

        with st.form("add_transaction_form"):

            transaction = Transaction()
            if t:
                st.text_input(label="Trade", value=f"{t.type} {t.quantity} of {t.instrument.name} on {t.date}", disabled=True)
            selected_account = st.selectbox(
                "Account",
                list(accounts_map.keys()),
                index=selected_account_index
            )
            selected_type = st.selectbox(
                "Transaction Type",
                options=["fee", "div", "tax"],
            )
            transaction_date = st.date_input("Transaction date", value=transaction_date_default)
            transaction_time = st.time_input("Transaction time", value=transaction_time_default, step=60)
            amount = st.number_input("Amount (€)", min_value=0.0, step=0.01)
            description = st.text_area("Description")

            col1, col2 = st.columns([7,1])
            with col2:
                save = st.form_submit_button("💾 Save")

            if save:
                # TODO: add validation
                if not transaction_date:
                    st.warning("Date cannot be empty.")
                elif not transaction_time:
                    st.warning("Time cannot be empty.")
                elif amount <= 0:
                    st.warning("Amount must be greater than zero.")
                else:
                    try:
                        transaction.account_id = accounts_map.get(selected_account).id
                        if t:
                            transaction.trade_id = t.id
                        transaction.date = datetime.combine(transaction_date, transaction_time).replace(tzinfo=get_timezone())
                        transaction.type = selected_type
                        transaction.amount = write_to_db(amount)
                        transaction.description = description
                        session.add(transaction)
                        session.commit()
                        st.session_state.transaction_id = None
                        st.success("✅ Transaction saved successfully!")
                    except Exception as e:
                        st.error(f"Error saving transaction: {e}")

    col1, col2 = st.columns([5,1])
    with col2:
        if st.button("Back to list"):
            st.session_state.trade_id = None
            st.switch_page("pages/transactions_list.py")