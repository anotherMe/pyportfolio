import streamlit as st
from lib.db import get_session
from lib.portfolio import get_position
from lib.models import Instrument

st.set_page_config(page_title="My Portfolio Dashboard", layout="wide", initial_sidebar_state="expanded")

st.title("📈 Portfolio Overview")

session = get_session()
instruments = session.query(Instrument).all()

data = []
for inst in instruments:
    qty, avg_price = get_position(session, inst.id)
    if qty > 0:
        data.append({
            "ISIN": inst.isin,
            "Qty": qty,
            "Avg Price (€)": avg_price / 100,
        })

st.dataframe(data, use_container_width=True)
st.markdown("Navigate via the sidebar to manage trades, instruments, or taxes.")
