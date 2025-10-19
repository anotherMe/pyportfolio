
import streamlit as st
from lib.database import get_session
from lib.instruments_repository import get_all_instruments
import pandas as pd


print("Running instruments list page...")

st.session_state.instrument_id = None  # Always reset selected instrument ID


st.title("🔧 Instruments")
st.subheader("Instruments list")

with get_session() as session, session.begin():
        
    instruments = get_all_instruments(session)

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
            "Yahoo": f"https://finance.yahoo.com/quote/{inst.ticker}" if inst.ticker else "",
            "Details": f"/instruments_details/?instrument_id={inst.id}",
        })

    df = pd.DataFrame(data)

    # --- Configure columns ---
    column_config = {
        "Yahoo": st.column_config.LinkColumn(
            "Yahoo",
            help="Click ticker to open Yahoo Finance",
            display_text=":material/table_chart_view:",
            width=2
        ),
        "Details": st.column_config.LinkColumn(
            "Detail",
            help="Click to open Instrument detail page",
            display_text=":material/edit:",
            width=2
        )
    }

    # --- Display table ---
    st.data_editor(
        df.drop(columns=["ID"]),
        hide_index=True,
        column_config=column_config,
        disabled=True  # read-only table
    )

