
import streamlit as st
from lib.repo.accounts_repository import get_account_by_name, get_all_accounts
from lib.database import read_from_db, get_session
from lib.models import Instrument
import pandas as pd

from lib.streamlit.utils import account_selector
from lib.repo.trades_repository import get_all_trades

print("Running trades page...")

st.title("💼 Trades")

if 'trade_id' not in st.session_state:
    st.session_state.trade_id = None

with get_session() as session:

    # --- Account selector ---
    accounts = get_all_accounts(session)
    account_selector(accounts) # Show sidebar account selector
    current_account = get_account_by_name(session, st.session_state.account)

    # --- Fetch data ---
    instruments = session.query(Instrument).all()
    instrument_map = {inst.name: inst for inst in instruments}
    trades = get_all_trades(session, current_account)
    
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

                col1, col2, col3 = st.columns([1,1,1])
                col1.write(f"Account: {trade.account.name}")
                col2.write(f"Instrument: {trade.instrument.name}")
                col3.write(f"ISIN: {trade.instrument.isin}")
                
                col1, col2, col3, col4 = st.columns([3,1,1,1])
                col1.write(f"Date: {trade.date.strftime('%Y-%m-%d %H:%M')}")
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
                        st.warning("Delete functionality is not implemented yet.")
                        # session.delete(trade)
                        # st.success("Trade deleted.")

                # --- Related transactions ---
                st.divider()
                st.write("Transactions:")
                if trade.transactions:                        
                    txn_details = [{
                        "Type": txn.type,
                        "Amount (€)": f"{read_from_db(txn.amount):.2f}",
                        "Date": txn.date.strftime('%Y-%m-%d')
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
                