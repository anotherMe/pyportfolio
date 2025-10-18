
import streamlit as st
from lib.database import from_cents, get_session
from lib.models import Instrument, Trade
import pandas as pd

print("Running trades page...")

st.title("💼 Trades")

if 'trade_id' not in st.session_state:
    st.session_state.trade_id = None

with get_session() as session:

    # --- Fetch data ---
    instruments = session.query(Instrument).all()
    instrument_map = {inst.name: inst for inst in instruments}
    trades = session.query(Trade).join(Trade.instrument).order_by(Trade.date).all()
    latest_trades = session.query(Trade).join(Trade.instrument).order_by(Trade.date.desc()).limit(10).all()


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
        filtered_trades = trades

    st.divider()
    
    if filtered_trades:
        for trade in filtered_trades:
            with st.container(border=True):

                col1, col2, col3 = st.columns([1,1,1])
                col1.write(f"Instrument: {trade.instrument.name}")
                col2.write(f"ISIN: {trade.instrument.isin}")
                col3.write(f"Date: {trade.date.strftime('%Y-%m-%d %H:%M')}")
                
                col1, col2, col3 = st.columns([1,1,1])
                col1.write(trade.type)
                col2.write(trade.quantity)
                col3.write(f"{trade.price / 100:.2f} €")

                col1, col2, col3 = st.columns([5,1,1])
                with col2:
                    if st.button("✏️ Edit", key=f"edit_{trade.id}"):
                        st.session_state.trade_id = trade.id
                        st.switch_page("pages/trades_edit.py")
                with col3:
                    if st.button("🗑️ Delete", key=f"delete_{trade.id}"):
                        st.warning("Delete functionality is not implemented yet.")
                        # session.delete(trade)
                        # st.success("Trade deleted.")

                if trade.transactions:                        
                    st.divider()
                    st.write("Related Transactions:")
                    if trade.transactions:
                        txn_details = [{
                            "Type": txn.type,
                            "Amount (€)": f"{from_cents(txn.amount):.2f}",
                            "Date": txn.date.strftime('%Y-%m-%d')
                        } for txn in trade.transactions]
                        st.dataframe(pd.DataFrame(txn_details))
                        
    else:
        st.info("No trades available.")
                