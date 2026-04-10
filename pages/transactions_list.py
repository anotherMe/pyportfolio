
import streamlit as st
from lib.repo.accounts_repository import get_account_by_name
from lib.database import get_session, read_from_db
from lib.models import Transaction, Instrument
from lib.utils import confirm_delete_dialog
from service.utils import to_local
import lib.repo.transactions_repository as transactions_repo

from logging_config import setup_logger
log = setup_logger(__name__)

log.debug("Running transactions page...")

def delete_transaction(item_id):
    with get_session() as session, session.begin():
        try:
            transactions_repo.delete_transaction(session, item_id)
            session.commit()
        except Exception:
            log.exception("")
            st.error(f"Error while deleting item {item_id}")

st.title("💰 Transactions")

with get_session() as session:

    current_account = get_account_by_name(session, st.session_state.account)

    # --- Transaction type selector
    transaction_type = st.selectbox(
        "Transaction Type",
        options=["All", "div", "tax", "fee"],
        disabled=False
    )

    instruments = session.query(Instrument).order_by(Instrument.isin).all()
    if not instruments:
        st.info("No instruments found. Please add instruments first.")
        st.stop()

    isin_map = {f"{inst.isin} — {inst.name or inst.ticker or ''}".strip(): inst.id for inst in instruments}
    isin_options = list(isin_map.keys())
        
    st.subheader("Transactions")

    if transaction_type == "All":
        transactions = transactions_repo.get_all_transactions(session, current_account)
    else:
        transactions = session.query(Transaction).where(Transaction.type == transaction_type).order_by(Transaction.date.desc()).all()

    if not transactions:
        st.info("No transactions recorded yet.")
        st.stop()

    st_dataframe = st.dataframe(data=[
        {
            "Type": t.type,
            "Instrument": t.position.instrument.name if t.position else "",
            "Date": to_local(t.date),
            "Amount": f"{read_from_db(t.amount):.2f} {t.position.instrument.currency.symbol if t.position and t.position.instrument and t.position.instrument.currency else '€'}",
            "Description": t.description or ""
        } for t in transactions
    ],
    on_select="rerun", 
    selection_mode="single-row")

    if st_dataframe["selection"]["rows"]:
        dataframe_index = st_dataframe["selection"]["rows"][0]
        selected_transaction: Transaction = transactions[dataframe_index]
        with st.container(horizontal=True):
            # st.space("stretch")
            if st.button("Detail"):
                st.session_state.transaction_id = selected_transaction.id
                st.switch_page("pages/transactions_detail.py")
            if st.button("Edit", type="secondary"):
                st.session_state.transaction_id = selected_transaction.id
                st.switch_page("pages/transactions_edit.py")
            if st.button("Delete", type="primary"):
                confirm_delete_dialog(f"Are you sure you want to delete transaction {selected_transaction.id} ?", selected_transaction.id, delete_transaction)
