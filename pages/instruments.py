import streamlit as st
from lib.db import get_average_buy_price, get_session
from lib.portfolio import add_instrument
from lib.models import Instrument

st.title("📊 Instruments")
session = get_session()

# Add new instrument
with st.form("add_instrument"):
    isin = st.text_input("ISIN")
    name = st.text_input("Name")
    ticker = st.text_input("Ticker")
    submitted = st.form_submit_button("Add Instrument")
    if submitted and isin:
        add_instrument(session, isin, name, ticker)
        session.commit()
        st.success(f"Added {name}")

# List instruments
st.subheader("All instruments")
instruments = session.query(Instrument).all()
array = []
for i in instruments:
    avg_buy_price = get_average_buy_price(session, i.id)
    array.append({
        "ISIN": i.isin,
        "Name": i.name,
        "Ticker": i.ticker,
        "Avg Buy Price (€)": avg_buy_price / 100 if avg_buy_price else None
    })

st.dataframe(array, use_container_width=True)
