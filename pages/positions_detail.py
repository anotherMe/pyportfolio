
import logging
import pandas as pd
import streamlit as st
from lib.database import read_from_db, get_session
from lib.models import Instrument, Position
import lib.repo.positions_repository as repo
from lib.utils import confirm_delete_dialog
from service.utils import to_local

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
st.subheader("Position Details")

if not st.session_state.position_id:
    st.write("No Position selected")
    if st.button("Back to list"):
        st.switch_page("pages/positions_list.py")
    st.stop()

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


        # --- Related Trades ---

        st.divider()
        st.write("Trades:")
        if position.trades:
            inst_trades = [{
                "Account": trade.account.name,
                "Type": "📥 Buy" if trade.type.lower() == "buy" else "📤 Sell" if trade.type.lower() == "sell" else trade.type,
                "Date": to_local(trade.date),
                "Qty": trade.quantity,
                "Price": read_from_db(trade.price)
            } for trade in inst.trades]
            st.dataframe(data=pd.DataFrame(inst_trades), hide_index=True)
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