
import streamlit as st
import pandas as pd

from lib.database import get_session
from lib.enums import TransactionType
from lib.repo.accounts_repository import get_account_by_name
from lib.utils import confirm_delete_dialog
from service.utils import to_local
from service.transactions_service import TransactionsService

from logging_config import setup_logger
log = setup_logger(__name__)

log.debug("Running transactions list page...")

transactions_service = TransactionsService()


def delete_transaction(item_id):
    with get_session() as session:
        try:
            transactions_service.delete(session, item_id)
        except Exception:
            log.exception("")
            st.error(f"Error while deleting transaction {item_id}")


st.title("💰 Transactions")

with get_session() as session:

    current_account = get_account_by_name(session, st.session_state.account)

    # --- Transaction type selector ---
    type_options = {"All": None} | {t.value: t for t in TransactionType}
    selected_label = st.selectbox("Transaction Type", options=list(type_options.keys()))
    selected_type = type_options[selected_label]

    if selected_type is None:
        transactions = transactions_service.get_all(session, current_account)
    else:
        transactions = transactions_service.get_by_type(session, selected_type, current_account)

    st.subheader("Transactions")

    if not transactions:
        st.info("No transactions recorded yet.")
        st.stop()

    st_dataframe = st.dataframe(
        data=pd.DataFrame([{
            "txn_id": t.id,
            "Type": t.type.value,
            "Instrument": t.instrument_name,
            "Date": to_local(t.date),
            "Amount": f"{t.amount:.2f} {t.currency_symbol}",
            "Description": t.description or "",
        } for t in transactions]),
        column_config={"txn_id": None},
        on_select="rerun",
        selection_mode="single-row",
    )

    if st_dataframe["selection"]["rows"]:
        dataframe_index = st_dataframe["selection"]["rows"][0]
        selected_transaction = transactions[dataframe_index]
        with st.container(horizontal=True):
            if st.button("Detail"):
                st.session_state.transaction_id = selected_transaction.id
                st.switch_page("pages/transactions_detail.py")
            if st.button("Edit", type="secondary"):
                st.session_state.transaction_id = selected_transaction.id
                st.switch_page("pages/transactions_edit.py")
            if st.button("Delete", type="primary"):
                confirm_delete_dialog(f"Are you sure you want to delete transaction {selected_transaction.id}?", selected_transaction.id, delete_transaction)
