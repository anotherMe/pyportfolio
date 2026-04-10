
import streamlit as st
import pandas as pd

from lib.database import get_session
from lib.utils import confirm_delete_dialog
from service.utils import to_local
from service.trades_service import TradesService
from service.transactions_service import TransactionsService

from logging_config import setup_logger
log = setup_logger(__name__)

log.debug("Running trades detail page...")

trades_service = TradesService()
transactions_service = TransactionsService()

if 'trade_id' not in st.session_state:
    st.session_state.trade_id = None


def delete_trade(item_id):
    with get_session() as session:
        try:
            trades_service.delete(session, item_id)
            st.switch_page("pages/trades_list.py")
        except Exception:
            log.exception("")
            st.error(f"Error while deleting trade {item_id}")


st.title("💼 Trades")

if not st.session_state.trade_id:
    st.write("No Trade selected")
    if st.button("Back to list"):
        st.switch_page("pages/trades_list.py")
    st.stop()

with get_session() as session:

    st.subheader("Trade details")

    trades = trades_service.get_all(session)
    trade = next((t for t in trades if t.id == st.session_state.trade_id), None)

    if trade is None:
        st.error("Trade not found.")
        st.stop()

    with st.container(border=True):

        col1, col2, col3 = st.columns([1, 1, 1])
        col1.write(f"Account: {trade.account_name}")
        col2.write(f"Instrument: {trade.instrument_name}")
        col3.write(f"ISIN: {trade.instrument_isin}")

        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
        col1.write(f"Date: {to_local(trade.date)}")
        col2.write(trade.type.value.upper())
        col3.write(trade.quantity)
        col4.write(f"{trade.price:.2f} {trade.currency_symbol}")

        col1, col2, col3 = st.columns([7, 1, 1])
        with col2:
            if st.button("✏️ Edit", key=f"edit_{trade.id}"):
                st.session_state.trade_id = trade.id
                st.switch_page("pages/trades_edit.py")
        with col3:
            if st.button("🗑️ Delete", key=f"delete_{trade.id}"):
                confirm_delete_dialog(f"Are you sure you want to delete trade {trade.id}?", trade.id, delete_trade)

        # --- Related transactions (linked to the same position) ---
        st.divider()
        st.write("Transactions (for this position):")
        position_transactions = transactions_service.get_by_position(session, trade.position_id)
        if position_transactions:
            txn_detail = [{
                "Type": t.type.value,
                "Amount": f"{t.amount:.2f} {t.currency_symbol}",
                "Date": to_local(t.date),
            } for t in position_transactions]
            st.dataframe(pd.DataFrame(txn_detail))
        else:
            st.info("No transactions available")

        cols = st.columns([5, 1])
        with cols[1]:
            if st.button("Add new transaction", key=f"add_trans_btn_{trade.id}"):
                st.session_state.position_id = trade.position_id
                st.switch_page("pages/transactions_edit.py")

with st.container(horizontal=True):
    st.space("stretch")
    if st.button("Back to list"):
        st.session_state.trade_id = None
        st.switch_page("pages/trades_list.py")
