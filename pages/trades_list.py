
import streamlit as st
import pandas as pd

from lib.database import get_session
from lib.utils import confirm_delete_dialog
from service.utils import to_local
from service.trades_service import TradesService
from service.transactions_service import TransactionsService

from logging_config import setup_logger
log = setup_logger(__name__)

log.debug("Running trades list page...")

st.title("Trades")

if 'show_editor' not in st.session_state:
    st.session_state.show_editor = False
if 'trade_id' not in st.session_state:
    st.session_state.trade_id = None

trades_service = TradesService()
transactions_service = TransactionsService()


def delete_trade(item_id):
    with get_session() as session:
        try:
            trades_service.delete(session, item_id)
        except Exception:
            log.exception("")
            st.error(f"Error while deleting trade {item_id}")


with get_session() as session:

    trades = trades_service.get_all(session)

    if not trades:
        st.info("No trades found")
        st.stop()

    # --- Search input ---
    search_term = st.text_input("🔍 Search by Instrument ISIN, Ticker, or Name").strip().lower()
    if search_term:
        filtered_trades = [
            t for t in trades
            if search_term in t.instrument_isin.lower()
            or search_term in t.instrument_ticker.lower()
            or search_term in t.instrument_name.lower()
        ]
    else:
        filtered_trades = trades

    st.subheader("Trades")

    if not filtered_trades:
        st.info("No trades corresponding to the current search")
        st.stop()

    df = pd.DataFrame([{
        "trade_id": t.id,
        "Instrument": t.instrument_name,
        "ISIN": t.instrument_isin,
        "Date": to_local(t.date),
        "Type": "➕ BUY" if t.type.value == "buy" else "➖ SELL",
        "Quantity": t.quantity,
        "Price": f"{t.price:.2f} {t.currency_symbol}",
    } for t in filtered_trades])

    st_dataframe = st.dataframe(
        data=df,
        column_config={
            "trade_id": None,
            "Instrument": "Instrument",
            "ISIN": "ISIN",
            "Date": "Date",
            "Type": "Type",
            "Quantity": "Quantity",
            "Price": "Price",
        },
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
    )

    if st_dataframe["selection"]["rows"]:
        dataframe_index = st_dataframe["selection"]["rows"][0]
        selected_trade = filtered_trades[dataframe_index]
        trade = selected_trade
        with st.container(border=True):
            col1, col2, col3 = st.columns([1, 1, 1])
            col1.write(f"**Account:** {trade.account_name}")
            col2.write(f"**Instrument:** {trade.instrument_name}")
            col3.write(f"**ISIN:** {trade.instrument_isin}")
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            col1.write(f"**Date:** {to_local(trade.date)}")
            col2.write(f"**Type:** {trade.type.value.upper()}")
            col3.write(f"**Qty:** {trade.quantity}")
            col4.write(f"**Price:** {trade.price:.2f} {trade.currency_symbol}")

            st.divider()
            st.write("**Transactions (for this position):**")
            position_transactions = transactions_service.get_by_position(session, trade.position_id)
            if position_transactions:
                st.dataframe(pd.DataFrame([{
                    "Type": t.type.value,
                    "Amount": f"{t.amount:.2f} {t.currency_symbol}",
                    "Date": to_local(t.date),
                } for t in position_transactions]), hide_index=True)
            else:
                st.info("No transactions available")
        with st.container(horizontal=True, horizontal_alignment="right"):
            if st.button("Delete", type="primary"):
                confirm_delete_dialog(f"Are you sure you want to delete trade {selected_trade.id}?", selected_trade.id, delete_trade)
            if st.button("Edit", type="secondary"):
                st.session_state.trade_id = selected_trade.id
                st.switch_page("pages/trades_edit.py")

    st.divider()
    with st.container(horizontal=True, horizontal_alignment="right"):
        if st.button("➕ Add New"):
            st.session_state["trade_id"] = None
            st.switch_page("pages/trades_edit.py")