
import streamlit as st
from lib.repo.accounts_repository import get_account_by_name, get_all_accounts
from lib.database import read_from_db, get_session
from lib.repo.instruments_repository import get_all_instruments
import pandas as pd

from service.utils import account_selector, to_local
from lib.repo.trades_repository import get_all_trades

from logging_config import setup_logger
log = setup_logger(__name__)

log.debug("Running trades page...")

st.title("💼 Trades")

if 'show_editor' not in st.session_state:
    st.session_state.show_editor = False
if 'trade_id' not in st.session_state:
    st.session_state.trade_id = None

with get_session() as session:

    # --- Account selector ---
    accounts = get_all_accounts(session)
    account_selector(accounts) # Show sidebar account selector
    current_account = get_account_by_name(session, st.session_state.account)

    # --- Fetch data ---
    instruments = get_all_instruments(session)
    instrument_map = {inst.name: inst for inst in instruments}
    trades = get_all_trades(session, current_account)
    # latest_trades = session.query(Trade).join(Trade.instrument).order_by(Trade.date.desc()).limit(10).all()

    if not trades:
        st.info("No trades found")
        st.stop()

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
        filtered_trades = trades

    
    # --------------------------------------------------------------------------------------------------------------

    st.subheader("Trades")
    
    if filtered_trades:
        latest_trade_details = [{
                                "trade_id": t.id,
                                "Instrument": t.instrument.name,
                                "ISIN": t.instrument.isin,
                                "Date": to_local(t.date),
                                "Type": "➕ BUY" if t.type.lower() == "buy" else "➖ SELL",
                                "Quantity": t.quantity,
                                "Price (€)": f"{read_from_db(t.price)}"
                            } for t in filtered_trades]
        
        cols = st.columns([2, 2, 2, 2, 2, 2, 2])
        headers = ["Instrument", "ISIN", "Date", "Type", "Quantity", "Price (€)", "Action"]
        for c, h in zip(cols, headers):
            c.markdown(f"**{h}**")

        # Data rows
        for row in latest_trade_details:
            cols = st.columns([2, 2, 2, 2, 2, 2, 2])
            cols[0].write(row["Instrument"])
            cols[1].write(row["ISIN"])
            cols[2].write(row["Date"])
            cols[3].write(row["Type"])
            cols[4].write(row["Quantity"])
            cols[5].write(row["Price (€)"])

            if cols[6].button("View", key=f"view_{row['ISIN']}_{row['Date']}"):
                st.session_state["trade_id"] = row["trade_id"]
                st.switch_page("pages/trades_edit.py")  # target page path

    else:
        st.info("No trades available for the current search")
        