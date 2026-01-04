
import logging
import pandas as pd
import streamlit as st
from lib.database import read_from_db, get_session
from lib.enums import Currency
from lib.models import Instrument, Position
import lib.repo.positions_repository as repo
from lib.utils import confirm_delete_dialog
from service import positions_service as service
from service.utils import format_currency, to_local

from logging_config import setup_logger
log = setup_logger(__name__)

log.debug("Running Positions details page...")

if "position_id" not in st.session_state:
    st.session_state.position_id = None

def delete_position(item_id):
    with get_session() as session, session.begin():
        try:
            repo.delete_position(session, item_id)
            session.commit()
        except Exception:
            logging.exception("")
            st.error(f"Error while deleting item {item_id}")


st.title("Positions")

if not st.session_state.position_id:
    st.write("No Position selected")
    if st.button("Back to list"):
        st.switch_page("pages/positions_list.py")
    st.stop()

st.subheader(f"Position {st.session_state.position_id} details")

with get_session() as session, session.begin():

    position = session.get(Position, st.session_state.position_id)
    inst = session.get(Instrument, position.instrument_id)

    with st.container(border=True):
        
        # --- Row: Name and Ticker ---
        st.subheader(inst.name)

        # --- Row: Long name ---
        if inst.name_long:
            stripped = inst.name_long.strip()
            st.markdown(f"**{stripped}**")

        # --- Row: ISIN and Ticker ---
        col1, col2, col3 = st.columns([2,1,3])
        if inst.isin:
            col1.write(f"**ISIN:** [{inst.isin}](https://www.justetf.com/en/etf-profile.html?isin={inst.isin})")
        if inst.ticker:
            col2.markdown(f"**Ticker**: [{inst.ticker}](https://finance.yahoo.com/quote/{inst.ticker})")

        # --- Row: Currency and Category ---
        col1, col2, col3 = st.columns([2,1,3])
        if inst.currency:
            col1.write(f"**Currency:** {inst.currency or '-'}")
        if inst.ticker:
            col2.markdown(f"**Category**: {inst.category}")

        # --- Row: Description ---
        if inst.description:
            st.write(inst.description)

        # # --- Row: empty ---
        # st.write(" ")

        # # --- Row: Button bar ---
        # col1, col2, col3 = st.columns([6, 1, 1])
        # with col2:
        #     if st.button("✏️ Edit", key=f"edit_{inst.id}"):
        #         st.session_state["position_id"] = inst.id
        #         st.switch_page("pages/instruments_edit.py")

        # with col3:
        #     if st.button("🗑️ Delete", key=f"delete_{position.id}"):
        #         confirm_delete_dialog(f"Are you sure you want to delete Position {position.id} ?", position.id, delete_position)

        with st.container(horizontal=True):
            st.space("stretch")
            if st.button("🗑️ Delete", key=f"delete_{position.id}"):
                confirm_delete_dialog(f"Are you sure you want to delete Position {position.id} ?", position.id, delete_position)

        # --- Row: Position details ---
        st.divider()
        st.subheader("Position details")
        
        position_summary = service.get_position_summary(session, position)
        with st.container(horizontal=False):
            st.write(f"**Position ID:** {position_summary.position_id}")
            st.write(f"**Account:** {position.account.name}")
            st.write(f"**Opening date:** {to_local(position_summary.opening_date)}")
            st.write(f"**Closing date:** {to_local(position_summary.closing_date) if position_summary.closing_date else 'N/A'}")
            st.write(f"**Remaining quantity:** {position_summary.remaining_quantity}")
            st.write(f"**Average buy price:** {format_currency(position_summary.avg_buy_price, Currency.from_code(inst.currency).symbol)}")
            st.write(f"**Total buy cost:** {format_currency(position_summary.total_buy_cost, Currency.from_code(inst.currency).symbol)}")
            st.write(f"**Realized PnL:** {format_currency(position_summary.realized_pnl, Currency.from_code(inst.currency).symbol)}")
            st.write(f"**Unrealized PnL:** {format_currency(position_summary.unrealized_pnl, Currency.from_code(inst.currency).symbol)}")
            st.write(f"**Total PnL:** {format_currency(position_summary.pnl, Currency.from_code(inst.currency).symbol)}")
            pnl_percent = position_summary.pnl_percent * 100 if position_summary.pnl_percent is not None else None
            st.write(f"**Total PnL %:** {pnl_percent:.2f} %" if pnl_percent is not None else "N/A")

        # --- Related Trades ---

        st.divider()
        st.write("Trades:")
        if position.trades:
            position_trades = [{
                "Account": trade.account.name,
                "Type": "📥 Buy" if trade.type.lower() == "buy" else "📤 Sell" if trade.type.lower() == "sell" else trade.type,
                "Date": to_local(trade.date),
                "Qty": trade.quantity,
                "Price": format_currency(read_from_db(trade.price), Currency.from_code(inst.currency).symbol),
                "Total": format_currency(read_from_db(trade.price) * trade.quantity, Currency.from_code(inst.currency).symbol)
            } for trade in position.trades]
            st.dataframe(data=pd.DataFrame(position_trades), hide_index=True)
        else:
            st.info("No trades available")
        cols = st.columns([5,1])
        with cols[1]:
            if st.button("Add new trade", key=f"add_trade_button_{inst.id}"):
                st.session_state.trade_id = None
                st.session_state.position_id = inst.id
                st.switch_page("pages/trades_edit.py")


        # --- Related Transactions ---

        st.divider()
        st.write("Transactions:")
        if position.transactions:                        
            txn_detail = [{
                "Type": txn.type,
                "Amount (€)": f"{read_from_db(txn.amount):.2f}",
                "Date": to_local(txn.date)
            } for txn in position.transactions]
            st.dataframe(pd.DataFrame(txn_detail))
        else:
            st.info("No transactions available")
        cols = st.columns([5,1])
        with cols[1]:
            if st.button("Add new transaction", key=f"add_trans_btn_{position.id}"):
                st.session_state.position_id = position.id
                st.switch_page("pages/transactions_edit.py")

    with st.container(horizontal=True):
        st.space("stretch")
        if st.button("Back to list"):
            st.switch_page("pages/positions_list.py")