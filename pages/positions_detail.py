
import pandas as pd
import streamlit as st

from lib.database import get_session
from lib.utils import confirm_delete_dialog
from service.instruments_service import InstrumentsService
from service.positions_service import PositionsService
from service.trades_service import TradesService
from service.transactions_service import TransactionsService
from service.utils import format_currency, format_currency_color, to_local

from logging_config import setup_logger
log = setup_logger(__name__)

log.debug("Running Positions details page...")

positions_service = PositionsService()
trades_service = TradesService()
transactions_service = TransactionsService()
instruments_service = InstrumentsService()


def delete_trade(item_id):
    with get_session() as session:
        try:
            trades_service.delete(session, item_id)
        except Exception:
            log.exception("")
            st.error(f"Error while deleting trade {item_id}")


def delete_transaction(item_id):
    with get_session() as session:
        try:
            transactions_service.delete(session, item_id)
        except Exception:
            log.exception("")
            st.error(f"Error while deleting transaction {item_id}")


if "position_id" not in st.session_state:
    st.session_state.position_id = None
if "trade_id" not in st.session_state:
    st.session_state.trade_id = None
if "transaction_id" not in st.session_state:
    st.session_state.transaction_id = None

st.title("Positions")

if not st.session_state.position_id:
    st.write("No Position selected")
    if st.button("Back to list"):
        st.switch_page("pages/positions_list.py")
    st.stop()

st.subheader(f"Position {st.session_state.position_id} details")

with get_session() as session:

    # Resolve position and instrument via service layer
    positions_basic = positions_service.get_all_basic(session)
    position_basic = next((p for p in positions_basic if p.id == st.session_state.position_id), None)

    if position_basic is None:
        st.error("Position not found.")
        st.stop()

    instruments = instruments_service.get_all(session)
    inst = next((i for i in instruments if i.id == position_basic.instrument_id), None)

    position_summary = positions_service.get_position_summary(session, st.session_state.position_id)

    currency_symbol = position_basic.instrument_symbol

    with st.container(border=True):

        # --- Instrument details ---
        with st.container(horizontal=True):
            st.subheader(position_basic.instrument_name)
            if st.button("Edit position"):
                st.session_state.position_id = position_basic.id
                st.session_state.instrument_id = position_basic.instrument_id
                st.switch_page("pages/positions_edit.py")

        if inst and inst.name_long:
            st.markdown(f"**{inst.name_long.strip()}**")

        col1, col2, col3 = st.columns([2, 1, 3])
        if inst and inst.isin:
            col1.write(f"**ISIN:** [{inst.isin}](https://www.justetf.com/en/etf-profile.html?isin={inst.isin})")
        if inst and inst.ticker:
            col2.markdown(f"**Ticker**: [{inst.ticker}](https://finance.yahoo.com/quote/{inst.ticker})")
        if inst and inst.currency:
            col1.write(f"**Currency:** {inst.currency.name} ({inst.currency.symbol})")
        if inst and inst.dist_policy:
            col2.markdown(f"**Category**: {inst.dist_policy.value}")
        if inst and inst.description:
            st.write(inst.description)

        # --- Position summary ---
        st.divider()
        col1, col2 = st.columns([1, 1])
        col1.write(f"**Account:** {position_basic.account_name}")
        col1.write(f"**Opening date:** {to_local(position_summary.opening_date)}")
        col1.write(f"**Closing date:** {to_local(position_summary.closing_date) if position_summary.closing_date else 'N/A'}")
        col1.write(f"**Remaining quantity:** {position_summary.remaining_quantity}")
        col1.write(f"**Total invested:** {format_currency(position_summary.total_invested, currency_symbol)}")

        col2.write(f"**Realized PnL:** {format_currency_color(position_summary.realized_pnl, currency_symbol)}")
        col2.write(f"**Transactions amount:** {format_currency_color(position_summary.transactions_amount, currency_symbol)}")
        col2.write(f"**Latest market price:** {format_currency(position_summary.latest_price, currency_symbol)} ( as of {to_local(position_summary.latest_price_date) if position_summary.latest_price_date else 'N/A'} )")
        col2.write(f"**Unrealized PnL:** {format_currency_color(position_summary.unrealized_pnl, currency_symbol)}")
        col2.write(f"**Total PnL:** {format_currency_color(position_summary.pnl, currency_symbol)}")
        pnl_percent = position_summary.pnl_percent * 100 if position_summary.pnl_percent is not None else None
        col2.write(f"**Total PnL %:** {pnl_percent:.2f} %" if pnl_percent is not None else "N/A")

        # --- Trades ---
        st.divider()
        st.subheader("Trades:")

        position_trades = trades_service.get_by_position(session, st.session_state.position_id)

        if position_trades:
            trades_df = pd.DataFrame([{
                "trade_id": t.id,
                "Date": to_local(t.date),
                "Type": "➕ BUY" if t.type.value == "buy" else "➖ SELL",
                "Qty": t.quantity,
                "Price": format_currency(t.price, currency_symbol),
                "Total": format_currency(t.price * t.quantity, currency_symbol),
            } for t in position_trades])

            trades_dataframe = st.dataframe(
                data=trades_df,
                column_config={"trade_id": None},
                hide_index=True,
                on_select="rerun",
                selection_mode="single-row",
            )

            if trades_dataframe["selection"]["rows"]:
                dataframe_index = trades_dataframe["selection"]["rows"][0]
                selected_trade = position_trades[dataframe_index]
                with st.container(horizontal=True):
                    if st.button("Detail", key="trade_detail_btn"):
                        st.session_state.trade_id = selected_trade.id
                        st.switch_page("pages/trades_detail.py")
                    if st.button("Edit", type="secondary", key="trade_edit_btn"):
                        st.session_state.trade_id = selected_trade.id
                        st.switch_page("pages/trades_edit.py")
                    if st.button("Delete", type="primary", key="trade_delete_btn"):
                        confirm_delete_dialog(f"Are you sure you want to delete trade {selected_trade.id}?", selected_trade.id, delete_trade)
        else:
            st.info("No trades available")

        cols = st.columns([5, 1])
        with cols[1]:
            if st.button("Add new trade", key=f"add_trade_button_{position_basic.id}"):
                st.session_state.trade_id = None
                st.session_state.position_id = position_basic.id
                st.switch_page("pages/trades_edit.py")

        # --- Transactions ---
        st.divider()
        st.write("Transactions:")

        position_transactions = transactions_service.get_by_position(session, st.session_state.position_id)

        if position_transactions:
            txn_df = pd.DataFrame([{
                "txn_id": t.id,
                "Type": t.type.value,
                "Amount": f"{t.amount:.2f} {currency_symbol}",
                "Date": to_local(t.date),
            } for t in position_transactions])

            transactions_dataframe = st.dataframe(
                data=txn_df,
                column_config={"txn_id": None},
                hide_index=True,
                on_select="rerun",
                selection_mode="single-row",
            )

            if transactions_dataframe["selection"]["rows"]:
                dataframe_index = transactions_dataframe["selection"]["rows"][0]
                selected_transaction = position_transactions[dataframe_index]
                with st.container(horizontal=True):
                    if st.button("Detail", key="txn_detail_btn"):
                        st.session_state.transaction_id = selected_transaction.id
                        st.switch_page("pages/transactions_detail.py")
                    if st.button("Edit", type="secondary", key="txn_edit_btn"):
                        st.session_state.transaction_id = selected_transaction.id
                        st.switch_page("pages/transactions_edit.py")
                    if st.button("Delete", type="primary", key="txn_delete_btn"):
                        confirm_delete_dialog(f"Are you sure you want to delete transaction {selected_transaction.id}?", selected_transaction.id, delete_transaction)
        else:
            st.info("No transactions available")

        cols = st.columns([5, 1])
        with cols[1]:
            if st.button("Add new transaction", key=f"add_trans_btn_{position_basic.id}"):
                st.session_state.position_id = position_basic.id
                st.switch_page("pages/transactions_edit.py")

    with st.container(horizontal=True):
        st.space("stretch")
        if st.button("Back to list"):
            st.switch_page("pages/positions_list.py")
