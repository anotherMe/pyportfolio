
import streamlit as st
from lib.database import get_session
from lib.models import Instrument


print("Running instruments edit page...")

st.title("🔧 Instruments")

if 'instrument_id' not in st.session_state:
    st.session_state.instrument_id = None


with get_session() as session, session.begin():
    
    if st.session_state.instrument_id:
        st.subheader("Edit Instrument")
        inst = session.get(Instrument, st.session_state.instrument_id)
        if not inst:
            st.error("Instrument not found.")
        else:
            
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
                    elif not inst.name:
                        st.warning("Name cannot be empty.")
                    else:
                        session.add(inst)
                        st.success("✅ Instrument saved successfully!")

    else:
        st.subheader("Add New Instrument")
        inst = Instrument()
        
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
                elif not inst.name:
                    st.warning("Name cannot be empty.")
                else:
                    session.add(inst)
                    st.success("✅ Instrument saved successfully!")
    
    col1, col2 = st.columns([9,1])
    with col2:
        if st.button("Back"):
            st.switch_page("pages/instruments_list.py")

