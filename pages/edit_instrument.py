import streamlit as st
from lib.db import get_session
from lib.models import Instrument

st.title("✏️ Edit Instrument")

session = get_session()

# retrieve instrument ID from session state or None
instrument_id = st.session_state.get("instrument_id", None)
if instrument_id is None:
    st.subheader("Add New Instrument")
    inst = Instrument()
else:
    inst = session.get(Instrument, int(instrument_id))
    if not inst:
        st.error("Instrument not found.")
        st.stop()
    st.subheader(f"Editing: {inst.name or inst.ticker or inst.isin}")

# --- Instrument form ---
with st.form("instrument_form"):
    inst.isin = st.text_input("ISIN", value=inst.isin or "")
    inst.ticker = st.text_input("Ticker", value=inst.ticker or "")
    inst.name = st.text_input("Name", value=inst.name or "")
    inst.currency = st.text_input("Currency", value=inst.currency or "EUR")

    save = st.form_submit_button("💾 Save")

    if save:
        if not inst.isin:
            st.warning("ISIN cannot be empty.")
        else:
            session.add(inst)
            session.commit()
            st.success("✅ Instrument saved successfully!")
            st.page_link("pages/instruments.py", label="⬅ Back to Instruments")
