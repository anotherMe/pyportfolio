import streamlit as st
import pandas as pd

from lib.database import get_session, read_from_db
from lib.portfolio_repository import compute_fifo_pnl

st.title("Trades (FIFO PnL)")

with get_session() as session:
    results = compute_fifo_pnl(session)

    data = []
    for r in results:
        t = r["trade"]
        data.append({
            "Instrument": t.instrument.name,
            "Date": t.date,
            "Type": t.type,
            "Quantity": t.quantity,
            "Sell Price (€)": read_from_db(t.price),
            "Avg Buy Price (€)": read_from_db(r["avg_buy_price"]),
            "PnL (€)": read_from_db(r["pnl"]),
        })

    df = pd.DataFrame(data).sort_values("Date")

    st.dataframe(
        df.style.format({
            "Sell Price (€)": "{:.2f}",
            "Avg Buy Price (€)": "{:.2f}",
            "PnL (€)": "{:.2f}",
        }).apply(
            lambda s: [
                "color: green" if v > 0 else "color: red" if v < 0 else ""
                for v in s
            ] if s.name == "PnL (€)" else [""] * len(s)
        )
    )
