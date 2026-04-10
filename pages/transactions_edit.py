
from datetime import datetime

import streamlit as st

from lib.database import get_session
from lib.enums import TransactionType
from lib.settings_manager import get_timezone
from service.accounts_service import AccountsService
from service.transactions_service import TransactionsService
from service.dtos import TransactionCreateDTO

from logging_config import setup_logger
log = setup_logger(__name__)

log.debug("Running transactions edit page...")

st.title("💰 Transactions")

if 'transaction_id' not in st.session_state:
    st.session_state.transaction_id = None
if 'position_id' not in st.session_state:
    st.session_state.position_id = None

accounts_service = AccountsService()
transactions_service = TransactionsService()

with get_session() as session:

    accounts = accounts_service.get_all(session)
    accounts_map = {acc.name: acc for acc in accounts}

    if st.session_state.transaction_id:

        transaction = next(
            (t for t in transactions_service.get_all(session) if t.id == st.session_state.transaction_id),
            None,
        )

        if transaction is None:
            st.error("Transaction not found.")
            st.stop()

        with st.container(horizontal=True):
            st.subheader(f"Editing Transaction with ID: {transaction.id}")
            if st.button("Clear selection"):
                st.session_state.transaction_id = None
                st.session_state.position_id = None
                st.rerun()

        with st.form("dividend_form"):
            selected_account = st.selectbox(
                "Account",
                list(accounts_map.keys()),
                index=list(accounts_map.keys()).index(transaction.account_name) if transaction.account_name in accounts_map else 0,
            )
            transaction_type = st.selectbox(
                "Transaction Type",
                options=list(TransactionType),
                format_func=lambda t: t.value,
                index=list(TransactionType).index(transaction.type),
            )
            transaction_datetime = st.date_input("Transaction date", value=transaction.date)
            transaction_time = st.time_input("Transaction time", value=transaction.date.time(), step=60)
            amount = st.number_input("Amount (€)", min_value=0.0, step=0.01, value=transaction.amount)
            submitted = st.form_submit_button("Save Transaction")

            if submitted:
                try:
                    dto = TransactionCreateDTO(
                        account_id=accounts_map[selected_account].id,
                        position_id=transaction.position_id,
                        date=datetime.combine(transaction_datetime, transaction_time).replace(tzinfo=get_timezone()),
                        type=transaction_type,
                        amount=amount,
                        description=transaction.description,
                    )
                    transactions_service.update(session, transaction.id, dto)
                    st.success(f"Transaction {transaction.id} updated successfully!")
                except Exception as e:
                    log.exception("")
                    st.error(f"Error updating transaction: {e}")

    else:

        position = None
        selected_account_index = 0

        if st.session_state.position_id:
            st.subheader(f"Add new transaction for position ID: {st.session_state.position_id}")
            # Resolve account from the position via repo (read-only, no service needed for this lookup)
            from lib.models import Position as PositionModel
            position = session.get(PositionModel, st.session_state.position_id)
            if position:
                account_name = position.account.name
                if account_name in accounts_map:
                    selected_account_index = list(accounts_map.keys()).index(account_name)
        else:
            st.subheader("Add new transaction")

        with st.form("add_transaction_form"):

            selected_account = st.selectbox(
                "Account",
                list(accounts_map.keys()),
                index=selected_account_index,
            )
            selected_type = st.selectbox(
                "Transaction Type",
                options=list(TransactionType),
                format_func=lambda t: t.value,
            )
            transaction_datetime = st.datetime_input("Transaction date", value=datetime.now())
            amount = st.number_input("Amount (€)", min_value=0.0, step=0.01)
            description = st.text_area("Description")

            col1, col2 = st.columns([7, 1])
            with col2:
                save = st.form_submit_button("💾 Save")

            if save:
                if not transaction_datetime:
                    st.warning("Date cannot be empty.")
                elif amount <= 0:
                    st.warning("Amount must be greater than zero.")
                else:
                    try:
                        dto = TransactionCreateDTO(
                            account_id=accounts_map[selected_account].id,
                            position_id=st.session_state.position_id,
                            date=transaction_datetime.replace(tzinfo=get_timezone()),
                            type=selected_type,
                            amount=amount,
                            description=description or None,
                        )
                        transactions_service.create(session, dto)
                        st.session_state.transaction_id = None
                        st.success("✅ Transaction saved successfully!")
                    except Exception as e:
                        log.exception("")
                        st.error(f"Error saving transaction: {e}")

    col1, col2 = st.columns([5, 1])
    with col2:
        if st.button("Back to list"):
            st.session_state.transaction_id = None
            st.session_state.position_id = None
            st.switch_page("pages/transactions_list.py")
