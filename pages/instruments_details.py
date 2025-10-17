
import streamlit as st
from lib.database import get_session
from lib.instruments_repository import delete_instrument, get_all_instruments


print("Running instruments details page...")

st.title("🔧 Instruments")
st.subheader("Instrument Details")

if 'instrument_id' not in st.session_state:
    st.session_state.instrument_id = None


with get_session() as session, session.begin():

    instruments = get_all_instruments(session)

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
            with st.container(border=True):
                
                # --- Row 1: Name and Ticker ---
                col1, col2 = st.columns([2,3])
                col1.subheader(inst.name)

                # --- Row 2: ISIN and Currency ---
                col1, col2, col3, col4 = st.columns([2, 1, 5, 2])
                col1.write(f"**ISIN:** {inst.isin}")
                if inst.ticker:
                    col2.markdown(f"[{inst.ticker}](https://finance.yahoo.com/quote/{inst.ticker})")
                else:
                    col2.write("-")
                col4.write(f"**Currency:** {inst.currency or '-'}")

                # --- Row 3: Additional info (example: description, last price) ---
                # col1, col2, col3 = st.columns([2, 2, 1])
                # col1.write(f"**Description:** {inst.description or '-'}")
                # col2.write(f"**Last Price:** {inst.last_price or '-'}")

                st.write("Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.")

                # --- Row 4: Button bar ---
                col1, col2, col3 = st.columns([6, 1, 1])  # last column small for button
                with col2:
                    if st.button("🗑️ Delete", key=f"delete_{inst.id}"):
                        delete_instrument(session, inst.id)
                        st.success("Instrument deleted successfully!")
                        st.session_state.active_tab = "List"
                        st.rerun()
                with col3:
                    if st.button("✏️ Edit", key=f"edit_{inst.id}"):
                        st.session_state["instrument_id"] = inst.id
                        st.switch_page("pages/instruments_edit.py")
