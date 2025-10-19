
import streamlit as st
from lib.database import get_session
from lib.instruments_repository import get_all_instruments
from lib.models import Instrument, Trade
import pandas as pd

from lib.streamlit.account_selector import extract_current_account_from_params
from lib.trades_repository import get_all_trades

print("Running trades page...")

st.title("💼 Trades")

if 'show_editor' not in st.session_state:
    st.session_state.show_editor = False
if 'trade_id' not in st.session_state:
    st.session_state.trade_id = None

with get_session() as session:

    current_account = extract_current_account_from_params(session)

    # --- Fetch data ---
    instruments = get_all_instruments(session, current_account)
    instrument_map = {inst.name: inst for inst in instruments}
    trades = get_all_trades(session, current_account)
    # latest_trades = session.query(Trade).join(Trade.instrument).order_by(Trade.date.desc()).limit(10).all()

    st.subheader("Latest Trades")
    
    if trades:
        latest_trade_details = [{
                                "Instrument": t.instrument.name,
                                "ISIN": t.instrument.isin,
                                "Date": t.date.strftime("%Y-%m-%d %H:%M"),
                                "Type": "➕ BUY" if t.type.lower() == "buy" else "➖ SELL",
                                "Quantity": t.quantity,
                                "Price (€)": f"{t.price / 100:.2f}"
                            } for t in trades]
        df_latest = pd.DataFrame(latest_trade_details)
        st.dataframe(data=df_latest, hide_index=True)
    else:
        st.info("No trades available.")
        
