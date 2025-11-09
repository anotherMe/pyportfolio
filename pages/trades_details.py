
import logging
import streamlit as st
from lib.enums import Currency
import lib.repo.accounts_repository as accounts_repo
import lib.repo.trades_repository as trades_repo
from lib.database import read_from_db, get_session
from lib.models import Instrument
import pandas as pd

from lib.utils import confirm_delete_dialog
from service.utils import account_selector, to_local

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

    # --- Account selector ---
    accounts = accounts_repo.get_all_accounts(session)
    account_selector(accounts) # Show sidebar account selector
    current_account = accounts_repo.get_account_by_name(session, st.session_state.account)

    # --- Fetch data ---
    instruments = session.query(Instrument).all()
    instrument_map = {inst.name: inst for inst in instruments}
    trades = trades_repo.get_all_trades(session, current_account)
    
    if not trades:
        st.info("No trades available")
        st.stop()

    st.subheader("Trade Details")

    # --- Search input ---
    search_term = st.text_input("🔍 Search by Instrument ISIN, Ticker, or Name").strip().lower()
    if search_term:
        filtered_trades = [
            trade for trade in trades
            if search_term in (trade.instrument.isin or "").lower()
            or search_term in (trade.instrument.ticker or "").lower()
            or search_term in (trade.instrument.name or "").lower()
        ]
    else:
        filtered_trades = []

    st.divider()
    
    if filtered_trades:
        for trade in filtered_trades:
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
                    txn_details = [{
                        "Type": txn.type,
                        "Amount (€)": f"{read_from_db(txn.amount):.2f}",
                        "Date": to_local(txn.date)
                    } for txn in trade.transactions]
                    st.dataframe(pd.DataFrame(txn_details))
                else:
                    st.info("No transactions available")
                cols = st.columns([5,1])
                with cols[1]:
                    if st.button("Add new transaction", key=f"add_trans_btn_{trade.id}"):
                        st.session_state.trade_id = trade.id
                        st.switch_page("pages/transactions_edit.py")
    else:
        st.info("No trades found for the current search")
                