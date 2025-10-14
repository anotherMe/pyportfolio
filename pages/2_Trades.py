import streamlit as st
from lib.db import get_session
from lib.portfolio import add_trade
from lib.models import Instrument

st.title("💼 Trades")
session = get_session()

instruments = session.query(Instrument).all()
instrument_map = {f"{i.name} ({i.ticker})": i for i in instruments}

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

st.subheader("Recent Trades")
for i in instruments:
    trades = i.trades
    if trades:
        st.markdown(f"### {i.name}")
        for t in trades:
            st.write(f"{t.date:%Y-%m-%d} | {t.type} | {t.quantity} @ {t.price/100:.2f}€")
