
import logging
import streamlit as st
from lib.enums import Currency
import lib.repo.trades_repository as trades_repo
from lib.database import read_from_db, get_session
from lib.models import Trade
import pandas as pd

from lib.utils import confirm_delete_dialog
from service.utils import to_local

print("Running trades page...")


if 'trade_id' not in st.session_state:
    st.session_state.trade_id = None

def delete_trade(item_id):
    with get_session() as session, session.begin():
        try:
            trades_repo.delete_trade(session, item_id)
            session.commit()
        except Exception:
            logging.exception("")
            st.error(f"Error while deleting item {item_id}")


st.title("💼 Trades")

with get_session() as session:

    st.subheader("Trade details")

    if not st.session_state.trade_id:
        st.write("No Trade selected")
        if st.button("Back to list"):
            st.switch_page("pages/trades_list.py")
        st.stop()

    trade = session.get(Trade, st.session_state.trade_id)
    with st.container(border=True):

        currency = Currency.from_code(trade.instrument.currency)

        col1, col2, col3 = st.columns([1,1,1])
        col1.write(f"Account: {trade.account.name}")
        col2.write(f"Instrument: {trade.instrument.name}")
        col3.write(f"ISIN: {trade.instrument.isin}")
        
        col1, col2, col3, col4 = st.columns([3,1,1,1])
        col1.write(f"Date: {to_local(trade.date)}")
        col2.write(trade.type)
        col3.write(trade.quantity)
        col4.write(f"{read_from_db(trade.price)} €")

        col1, col2, col3 = st.columns([7,1,1])
        with col2:
            if st.button("✏️ Edit", key=f"edit_{trade.id}"):
                st.session_state.trade_id = trade.id
                st.switch_page("pages/trades_edit.py")
        with col3:
            if st.button("🗑️ Delete", key=f"delete_{trade.id}"):
                confirm_delete_dialog(f"Are you sure you want to delete trade {trade.id} ?", trade.id, delete_trade)

        # --- Related transactions ---
        st.divider()
        st.write("Transactions:")
        if trade.transactions:                        
            txn_detail = [{
                "Type": txn.type,
                "Amount (€)": f"{read_from_db(txn.amount):.2f}",
                "Date": to_local(txn.date)
            } for txn in trade.transactions]
            st.dataframe(pd.DataFrame(txn_detail))
        else:
            st.info("No transactions available")
        cols = st.columns([5,1])
        with cols[1]:
            if st.button("Add new transaction", key=f"add_trans_btn_{trade.id}"):
                st.session_state.trade_id = trade.id
                st.switch_page("pages/transactions_edit.py")

with st.container(horizontal=True):
    st.space("stretch")
    if st.button("Back to list"):
        st.session_state.trade_id = None
        st.switch_page("pages/trades_list.py")