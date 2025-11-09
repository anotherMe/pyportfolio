
import streamlit as st
from lib.database import get_session
from lib.repo.instruments_repository import get_all_instruments
import pandas as pd


print("Running instruments list page...")

st.session_state.instrument_id = None  # Always reset selected instrument ID


st.title("🔧 Instruments")
st.subheader("Instruments list")

with get_session() as session:
    instruments = get_all_instruments(session)

if not instruments:
    st.info("No instruments found.")
    st.stop()

# --- Create dataframe ---
data = []
for inst in instruments:
    data.append({
        # "ID": inst.id,
        "ISIN": f"https://www.justetf.com/en/etf-profile.html?isin={inst.isin}" if inst.isin else "",
        "Ticker": f"https://finance.yahoo.com/quote/{inst.ticker}" if inst.ticker else "",
        "Name": inst.name,
        # "Currency": inst.currency or "",
    })

df = pd.DataFrame(data)

# --- Configure columns ---
column_config = {
    "ISIN": st.column_config.LinkColumn(
        help="Look up ISIN on JustETF site",
        display_text=r"[?&]isin=([^&#]+)"
    ),
    "Ticker": st.column_config.LinkColumn(
        help="Lookup ticker on Yahoo Finance site",
        display_text=r"/quote/([^/?#]+)"
    ),
}

# --- Display table ---
st.dataframe(
    data=df,
    hide_index=True,
    column_config=column_config,
)

