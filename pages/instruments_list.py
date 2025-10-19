
from math import e
import streamlit as st
from lib.database import get_session
from lib.instruments_repository import get_all_instruments
import pandas as pd

from lib.streamlit.account_selector import extract_current_account_from_params


print("Running instruments list page...")

st.session_state.instrument_id = None  # Always reset selected instrument ID


st.title("🔧 Instruments")
st.subheader("Instruments list")

with get_session() as session, session.begin():
        
    currenct_account = extract_current_account_from_params(session)
    instruments = get_all_instruments(session, currenct_account)

    if not instruments:
        st.info("No instruments found.")
        st.stop()


    data = []
    for inst in instruments:
        data.append({
            "ID": inst.id,
            "ISIN": inst.isin,
            "Ticker": inst.ticker,
            "Name": inst.name,
            "Currency": inst.currency or "",
            # External URL column
            "Ticker_URL": f"https://finance.yahoo.com/quote/{inst.ticker}" if inst.ticker else ""
        })

    df = pd.DataFrame(data)

    # --- Configure columns ---
    column_config = {
        "Ticker_URL": st.column_config.LinkColumn(
            "Yahoo Finance",
            help="Click ticker to open Yahoo Finance",
            display_text=":material/table_chart_view:"
        )
    }

    # --- Display table ---
    st.data_editor(
        df.drop(columns=["ID"]),
        hide_index=True,
        column_config=column_config,
        disabled=True  # read-only table
    )

