
import streamlit as st
from lib.repo.accounts_repository import get_account_by_name, get_all_accounts
from lib.database import read_from_db, get_session
from lib.repo.instruments_repository import get_all_instruments
import pandas as pd

from service.utils import account_selector
from lib.repo.trades_repository import get_all_trades

print("Running trades page...")

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

    st.subheader("Trades")
    
    if trades:
        latest_trade_details = [{
                                "Instrument": t.instrument.name,
                                "ISIN": t.instrument.isin,
                                "Date": t.date.strftime("%Y-%m-%d %H:%M"),
                                "Type": "➕ BUY" if t.type.lower() == "buy" else "➖ SELL",
                                "Quantity": t.quantity,
                                "Price (€)": f"{read_from_db(t.price)}"
                            } for t in filtered_trades]
        df_latest = pd.DataFrame(latest_trade_details)
        st.dataframe(data=df_latest, hide_index=True)
    else:
        st.info("No trades available for the current search")
        
