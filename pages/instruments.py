import streamlit as st
from lib.db import get_session
from lib.models import Instrument
import pandas as pd

st.title("📜 Instruments")

tab1, tab2, tab3 = st.tabs(["List", "Details", "Add New"])

session = get_session()
instruments = session.query(Instrument).order_by(Instrument.name).all()

with tab1:
    # --- Prepare data ---
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
        column_config=column_config,
        use_container_width=True,
        disabled=True  # read-only table
    )

with tab2:

    st.subheader("Instrument Details")
    # --- Search input ---
    search_term = st.text_input("🔍 Search by ISIN, Ticker, or Name").strip().lower()
    if search_term:
        filtered_instruments = [
            inst for inst in instruments
            if search_term in (inst.isin or "").lower()
            or search_term in (inst.ticker or "").lower()
            or search_term in (inst.name or "").lower()
        ]
    else:
        filtered_instruments = instruments

    if not filtered_instruments:
        st.info("No instruments found.")
    else:
        for inst in filtered_instruments:
            with st.container():
                st.divider()
                # --- Row 1: Name and Ticker ---
                col1, col2 = st.columns([3, 1])
                col1.subheader(inst.name)
                if inst.ticker:
                    col2.markdown(f"[{inst.ticker}](https://finance.yahoo.com/quote/{inst.ticker})")
                else:
                    col2.write("-")

                # --- Row 2: ISIN and Currency ---
                col1, col2 = st.columns([2, 1])
                col1.write(f"**ISIN:** {inst.isin}")
                col2.write(f"**Currency:** {inst.currency or '-'}")

                # --- Row 3: Additional info (example: description, last price) ---
                # col1, col2, col3 = st.columns([2, 2, 1])
                # col1.write(f"**Description:** {inst.description or '-'}")
                # col2.write(f"**Last Price:** {inst.last_price or '-'}")

                st.write("Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.")

                # --- Row 4: Edit button aligned to the right ---
                col1, col2 = st.columns([3, 1])  # last column small for button
                with col2:
                    if st.button("✏️ Edit", key=f"edit_{inst.id}"):
                        st.session_state["instrument_id"] = inst.id
                        st.switch_page("pages/edit_instrument.py")

# --- Add New Instrument button ---
st.divider()

# --- Add new instrument button ---
if st.button("Add New Instrument"):
    st.session_state["instrument_id"] = None
    st.switch_page("pages/edit_instrument.py")
