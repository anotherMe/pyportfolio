from datetime import datetime
import streamlit as st
from lib.db import get_session
from lib.portfolio import add_trade
from lib.models import Instrument, Trade
import pandas as pd

def load_data(session):
    instruments = session.query(Instrument).all()
    trades = session.query(Trade).join(Trade.instrument).order_by(Trade.date).all()
    latest_trades = session.query(Trade).join(Trade.instrument).order_by(Trade.date.desc()).limit(10).all()
    return instruments, trades, latest_trades

st.title("💼 Trades")
session = get_session()

# Load data
instruments, trades, latest_trades = load_data(session)
instrument_map = {f"{i.name} ({i.ticker})": i for i in instruments}

tab1, tab2, tab3 = st.tabs(["Latest", "Details", "Add New"])

with tab1:
    st.subheader("Latest Trades")
    if latest_trades:
        latest_trade_details = [{
            "Instrument": t.instrument.name,
            "ISIN": t.instrument.isin,
            "Date": t.date.strftime("%Y-%m-%d %H:%M"),
            "Type": t.type,
            "Quantity": t.quantity,
            "Price (€)": f"{t.price / 100:.2f}"
        } for t in latest_trades]
        df_latest = pd.DataFrame(latest_trade_details)
        st.dataframe(df_latest)
    else:
        st.info("No trades available.")
    

with tab2:
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

    if filtered_trades:
        for trade in filtered_trades:
            with st.container():
                col1, col2, col3 = st.columns([1,1,1])
                col1.write(f"Instrument: {trade.instrument.name}")
                col2.write(f"ISIN: {trade.instrument.isin}")
                col3.write(f"Date: {trade.date.strftime('%Y-%m-%d %H:%M')}")
                
                col1, col2, col3 = st.columns([1,1,1])
                col1.write(trade.type)
                col2.write(trade.quantity)
                col3.write(f"{trade.price / 100:.2f} €")

                col1, col2, col3 = st.columns([2,1,1])
                with col2:
                    if st.button("✏️ Edit", key=f"edit_{trade.id}"):
                        st.session_state["trade_id"] = trade.id
                        st.switch_page("pages/edit_trade.py")
                with col3:
                    if st.button("🗑️ Delete", key=f"delete_{trade.id}"):
                        session.delete(trade)
                        session.commit()
                        st.success("Trade deleted.")
                        st.experimental_rerun()
                st.divider()
    else:
        st.info("No trades available.")

with tab3:
    with st.form("add_trade"):
        selected_instrument = st.selectbox("Instrument", list(instrument_map.keys()))
        trade_type = st.selectbox("Type", ["buy", "sell"])
        qty = st.number_input("Quantity", min_value=1, step=1)
        price = st.number_input("Price (€)", min_value=0.0, step=0.01)
        date = st.date_input("Payment date", value=datetime.today())
        time = st.time_input("Payment time", value="now", step=60)
        fees = st.number_input("Fees (€)", min_value=0.0, step=0.01)
        tax_rate = st.number_input("Tax Rate (%)", min_value=0.0, max_value=100.0, step=0.1, value=26.0)
        notes = st.text_area("Notes", value="")
        submitted = st.form_submit_button("Add Trade")
        if submitted:
            inst = instrument_map[selected_instrument]
            add_trade(session, inst, trade_type, qty, price, fees, tax_rate, notes)
            session.commit()
            st.success(f"Trade added for {inst.name}")
            instruments, trades, latest_trades = load_data(session) # FIXME: not working
