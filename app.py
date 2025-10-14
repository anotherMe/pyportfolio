import streamlit as st
from lib.db import get_session
from lib.models import Instrument, Trade
from lib.portfolio import get_position, add_instrument, add_trade


st.set_page_config(page_title="My Portfolio", layout="wide")

st.title("📈 My Investment Portfolio")

session = get_session()

# --- Sidebar: add new instrument ---
st.sidebar.header("➕ Add Instrument")
with st.sidebar.form("add_instrument_form"):
    isin = st.text_input("ISIN")
    name = st.text_input("Name")
    ticker = st.text_input("Ticker")
    submitted = st.form_submit_button("Add Instrument")
    if submitted and isin:
        add_instrument(session, isin=isin, name=name, ticker=ticker)
        session.commit()
        st.success(f"Instrument {name} added!")

# --- Sidebar: add trade ---
st.sidebar.header("💼 Add Trade")
instruments = session.query(Instrument).all()
instrument_map = {f"{i.name} ({i.ticker})": i for i in instruments}
if instruments:
    with st.sidebar.form("add_trade_form"):
        inst_name = st.selectbox("Instrument", list(instrument_map.keys()))
        trade_type = st.selectbox("Type", ["buy", "sell"])
        quantity = st.number_input("Quantity", min_value=1, step=1)
        price = st.number_input("Price (EUR)", min_value=0.0, step=0.01)
        fees = st.number_input("Fees (EUR)", min_value=0.0, step=0.01)
        submit_trade = st.form_submit_button("Add Trade")
        if submit_trade:
            inst = instrument_map[inst_name]
            add_trade(session, inst, trade_type, quantity, price, fees)
            session.commit()
            st.success(f"Trade added for {inst.name}")

# --- Portfolio view ---
st.subheader("Current Portfolio")
data = []
for inst in instruments:
    qty, avg_price = get_position(session, inst.id)
    if qty > 0:
        last_trade = (
            session.query(Trade)
            .filter(Trade.instrument_id == inst.id)
            .order_by(Trade.date.desc())
            .first()
        )
        last_price = last_trade.price / 100 if last_trade else 0
        value = qty * last_price
        data.append({
            "Ticker": inst.ticker,
            "Name": inst.name,
            "Qty": qty,
            "Avg Price (€)": avg_price / 100,
            "Last Price (€)": last_price,
            "Value (€)": value,
        })

if data:
    st.dataframe(data, use_container_width=True)
else:
    st.info("No positions yet. Add your first trade!")

# --- Optional: portfolio total value ---
if data:
    total_value = sum(d["Value (€)"] for d in data)
    st.metric("💰 Total Portfolio Value", f"€ {total_value:,.2f}")
