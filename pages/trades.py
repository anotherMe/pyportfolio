import streamlit as st
from lib.db import get_session
from lib.portfolio import add_trade
from lib.models import Instrument
import pandas as pd

st.title("💼 Trades")
session = get_session()

instruments = session.query(Instrument).all()

tab1, tab2, tab3 = st.tabs(["List", "Details", "➕ Add New"])

with tab1:
    st.subheader("Recent Trades")
    trades_data = []
    for i in instruments:
        trades = i.trades
        if trades:
            for t in trades:
                trades_data.append({
                    "Instrument": i.name,
                    "Date": t.date.strftime("%Y-%m-%d %H:%M"),
                    "Type": t.type,
                    "Quantity": t.quantity,
                    "Price (€)": f"{t.price / 100:.2f}"
                })

    if trades_data:
        df = pd.DataFrame(trades_data)
        st.dataframe(df)
    else:
        st.write("No trades available.")

with tab2:
    st.subheader("Trade Details")
    instrument_map = {f"{i.name} ({i.ticker})": i for i in instruments}
    inst_label = st.selectbox("Select Instrument", list(instrument_map.keys()))
    if inst_label:
        inst = instrument_map[inst_label]
        trades = inst.trades
        if trades:
            trade_details = [{
                "Date": t.date.strftime("%Y-%m-%d"),
                "Type": t.type,
                "Quantity": t.quantity,
                "Price (€)": f"{t.price / 100:.2f}"
            } for t in trades]
            df = pd.DataFrame(trade_details)
            st.dataframe(df)
        else:
            st.info("No trades for this instrument.")

with tab3:
    with st.form("add_trade"):
        inst_label = st.selectbox("Instrument", list(instrument_map.keys()))
        trade_type = st.selectbox("Type", ["buy", "sell"])
        qty = st.number_input("Quantity", min_value=1, step=1)
        price = st.number_input("Price (€)", min_value=0.0, step=0.01)
        fees = st.number_input("Fees (€)", min_value=0.0, step=0.01)
        submitted = st.form_submit_button("Add Trade")
        if submitted:
            inst = instrument_map[inst_label]
            add_trade(session, inst, trade_type, qty, price, fees)
            session.commit()
            st.success(f"Trade added for {inst.name}")