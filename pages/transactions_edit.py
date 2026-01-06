

from datetime import datetime
import streamlit as st
from lib.repo.accounts_repository import get_all_accounts
from lib.database import read_from_db, get_session, write_to_db
from lib.models import Transaction, Position
from lib.settings_manager import get_timezone


print("Running transactions edit page...")

if 'transaction_id' not in st.session_state:
    st.session_state.transaction_id = None
if 'position_id' not in st.session_state:
    st.session_state.position_id = None


st.title("💰 Transactions")

with get_session() as session, session.begin():

    accounts = get_all_accounts(session)
    accounts_map = {account.name: account for account in accounts}

    if st.session_state.transaction_id:

        transaction = session.get(Transaction, st.session_state.transaction_id)
        st.subheader(f"Editing Transaction with ID: {transaction.id}")
    
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
            transaction_datetime = st.date_input("Transaction date", value=transaction.date)
            transaction_time = st.time_input("Transaction time", value=transaction.date.time(), step=60)
            amount = st.number_input("Amount (€)", min_value=0.0, step=0.01, value=read_from_db(transaction.amount))
            submitted = st.form_submit_button("Save Transaction")

            if submitted:
                # TODO: add validation
                transaction.account = accounts_map.get(selected_account)
                transaction.type = transaction_type
                transaction.date = datetime.combine(transaction_datetime, transaction_time).replace(tzinfo=get_timezone())
                transaction.amount = write_to_db(amount)
                session.add(transaction)
                st.success(f"Transaction for {transaction.id} updated successfully!")

    else:

        # --- Manage default values
        position = None
        selected_account_index = 0
        transaction_date_default = datetime.now()

        if st.session_state.position_id:  # Position ID coming from positions list page
            st.subheader(f"Add new transaction for position ID: {st.session_state.position_id}")
            position = session.get(Position, st.session_state.position_id)
            selected_account_index = list(accounts_map.keys()).index(position.account.name)
            # transaction_date_default = position.date.date()
            # transaction_time_default = position.date.time()
        else:
            st.subheader("Add new transaction")

        with st.form("add_transaction_form"):

            transaction = Transaction()
            # if position:
            #     st.text_input(label="Trade", value=f"{position.type} {position.quantity} of {position.instrument.name} on {position.date}", disabled=True)
            selected_account = st.selectbox(
                "Account",
                list(accounts_map.keys()),
                index=selected_account_index
            )
            selected_type = st.selectbox(
                "Transaction Type",
                options=["fee", "div", "tax"],
            )
            transaction_datetime = st.datetime_input("Transaction date", value=datetime.now())
            amount = st.number_input("Amount (€)", min_value=0.0, step=0.01)
            description = st.text_area("Description")

            col1, col2 = st.columns([7,1])
            with col2:
                save = st.form_submit_button("💾 Save")

            if save:
                # TODO: add validation
                if not transaction_datetime:
                    st.warning("Date cannot be empty.")
                elif amount <= 0:
                    st.warning("Amount must be greater than zero.")
                else:
                    try:
                        transaction.account_id = accounts_map.get(selected_account).id
                        if position:
                            transaction.position_id = position.id
                        transaction.date = transaction_datetime.replace(tzinfo=get_timezone())
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
            st.session_state.transaction_id = None
            st.session_state.position_id = None
            st.switch_page("pages/transactions_list.py")