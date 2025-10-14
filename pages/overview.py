import streamlit as st
from lib.db import get_session
from lib.portfolio import get_position
from lib.models import Instrument
import pandas as pd


st.title("📈 Portfolio Overview")

session = get_session()
instruments = session.query(Instrument).all()

data = []
for inst in instruments:
    qty, avg_price = get_position(session, inst.id)
    if qty > 0:
        # Create a link (using Markdown syntax)
        ticker_display = (
            f"[{inst.ticker}](https://finance.yahoo.com/quote/{inst.ticker})"
            if inst.ticker else ""
        )
        data.append({
            "ISIN": inst.isin,
            # "ticker": inst.ticker,
            "ticker": ticker_display,
            "Name": inst.name,
            "Qty": qty,
            "Avg Price (€)": avg_price / 100,
        })


# st.dataframe(data, use_container_width=True)
# if not data:
#     st.info("No positions yet. Add some trades!")

# Convert to DataFrame for display
df = pd.DataFrame(data)
# Streamlit's st.dataframe() doesn’t render markdown links, but st.markdown() does.
# So we use st.markdown with df.to_markdown() for clickable links.
st.markdown(df.to_markdown(index=False), unsafe_allow_html=True)