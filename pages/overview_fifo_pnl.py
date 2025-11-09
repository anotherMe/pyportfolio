import streamlit as st
import pandas as pd

from lib.enums import Currency
from lib.repo.accounts_repository import get_account_by_name, get_all_accounts
from lib.database import get_session, read_from_db
from lib.repo.portfolio_repository import compute_closed_positions
from service.utils import account_selector, to_local

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
        currency = Currency.from_code("EUR")
        data.append({
            "Instrument": t.instrument.name,
            "Date": to_local(t.date),
            "Type": t.type,
            "Quantity": t.quantity,
            f"Avg Buy Price ({currency.symbol})": read_from_db(r["avg_buy_price"]),
            f"Sell Price ({currency.symbol})": read_from_db(t.price),
            f"PnL ({currency.symbol})": read_from_db(r["pnl"]),
        })

    df = pd.DataFrame(data).sort_values("Date")

    st.dataframe(
        data=df.style.format({
            f"Sell Price ({currency.symbol})": "{:.2f}",
            f"Avg Buy Price ({currency.symbol})": "{:.2f}",
            f"PnL ({currency.symbol})": "{:.2f}",
        }).apply(
            lambda s: [
                "color: green" if v > 0 else "color: red" if v < 0 else ""
                for v in s
            ] if s.name == f"PnL ({currency.symbol})" else [""] * len(s)
        ),
        hide_index=True
    )
