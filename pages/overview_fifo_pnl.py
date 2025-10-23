import streamlit as st
import pandas as pd

from lib.repo.accounts_repository import get_account_by_name, get_all_accounts
from lib.database import get_session, read_from_db
from lib.repo.portfolio_repository import compute_closed_positions
from lib.streamlit.utils import account_selector

st.title("Trades (FIFO PnL)")

with get_session() as session:

    # --- Account selector ---
    accounts = get_all_accounts(session)
    account_selector(accounts) # Show sidebar account selector
    current_account = get_account_by_name(session, st.session_state.account)

    results = compute_closed_positions(session, current_account)

    data = []
    for r in results:
        t = r["trade"]
        data.append({
            "Instrument": t.instrument.name,
            "Date": t.date,
            "Type": t.type,
            "Quantity": t.quantity,
            "Avg Buy Price (€)": read_from_db(r["avg_buy_price"]),
            "Sell Price (€)": read_from_db(t.price),
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
