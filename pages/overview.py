import streamlit as st
from lib.database import from_cents, get_session
from lib.portfolio_repository import get_position
from lib.models import Instrument
import pandas as pd

print("Running overview page...")

st.title("📈 Portfolio Overview")

with get_session() as session:
        
    instruments = session.query(Instrument).all()

    if not instruments:
        st.info("No instruments yet. Add some instruments first!")
    else:
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
                    "ticker": ticker_display,
                    "Name": inst.name,
                    "Qty": qty,
                    "Avg Price": f"{avg_price} €",
                })

        df = pd.DataFrame(data)
        # Streamlit's st.dataframe() doesn’t render markdown links, but st.markdown() does.
        # So we use st.markdown with df.to_markdown() for clickable links.
        st.markdown(df.to_markdown(index=False), unsafe_allow_html=True)