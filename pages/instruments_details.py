
import pandas as pd
import streamlit as st
from lib.database import read_from_db, get_session
from lib.instruments_repository import delete_instrument, get_all_instruments


print("Running instruments details page...")

st.session_state.instrument_id = None  # Always reset selected instrument ID
if "ok_delete_instrument" not in st.session_state:
    st.session_state.ok_delete_instrument = False
if "show_delete_instrument_confirmation_dialog" not in st.session_state:
    st.session_state.show_delete_instrument_confirmation_dialog = False

@st.dialog("Confirm instrument deletion")
def confirm_delete_dialog():
    st.write("Are you sure you want to delete this instrument ?")
    col1, col2, col3 = st.columns([3,1,1])
    with col2:
        if st.button("✅ Yes"):
            st.session_state.ok_delete_instrument = True
            st.rerun()
    with col3:
        if st.button("❌ No"):
            st.session_state.show_delete_instrument_confirmation_dialog = False
            st.rerun()


st.title("🔧 Instruments")
st.subheader("Instrument Details")

with get_session() as session, session.begin():

    instruments = get_all_instruments(session)

    if not instruments:
        st.info("No instruments found.")
        st.stop()

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
        filtered_instruments = []

    if not filtered_instruments:
        st.info("No instruments found for the current search")
        st.stop()


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

            st.write(" ")  # just an empty row

            # --- Row 4: Button bar ---
            col1, col2, col3 = st.columns([7, 1, 1])  # last column small for button
            with col2:

                if not st.session_state.ok_delete_instrument:
                    if st.button("🗑️ Delete", key=f"delete_{inst.id}"):
                        st.session_state.show_delete_instrument_confirmation_dialog = True
                        st.rerun()
                else:
                    try:
                        delete_instrument(session, inst.id)
                        st.success("Instrument deleted successfully")
                        st.session_state.ok_delete_instrument = False  # VERY IMPORTANT: without this, it would keep deleting ALL instruments
                        st.session_state.show_delete_instrument_confirmation_dialog = False
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error deleting instrument: {e}")

                if st.session_state.show_delete_instrument_confirmation_dialog:
                    confirm_delete_dialog()

            with col3:
                if st.button("✏️ Edit", key=f"edit_{inst.id}"):
                    st.session_state["instrument_id"] = inst.id
                    st.switch_page("pages/instruments_edit.py")

            # --- Related trades ---
            st.divider()
            st.write("Trades:")
            if inst.trades:
                inst_trades = [{
                    "Account": trade.account.name,
                    "Type": "📥 Buy" if trade.type.lower() == "buy" else "📤 Sell" if trade.type.lower() == "sell" else trade.type,
                    "Date": trade.date,
                    "Qty": trade.quantity,
                    "Price": read_from_db(trade.price)
                } for trade in inst.trades]
                st.dataframe(data=pd.DataFrame(inst_trades), hide_index=True)
            else:
                st.info("No trades available")
            cols = st.columns([5,1])
            with cols[1]:
                if st.button("Add new trade", key=f"add_trade_button_{inst.id}"):
                    st.session_state.instrument_id = inst.id
                    st.switch_page("pages/trades_edit.py")