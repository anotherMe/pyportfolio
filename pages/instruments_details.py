
import logging
import pandas as pd
import streamlit as st
from lib.database import read_from_db, get_session
import lib.repo.instruments_repository as instruments_repo
from lib.utils import confirm_delete_dialog
from service.utils import to_local


print("Running instruments details page...")

if "instrument_id" not in st.session_state:
    st.session_state.instrument_id = None


def delete_instrument(item_id):
    with get_session() as session, session.begin():
        try:
            instruments_repo.delete_instrument(session, item_id)
            session.commit()
        except Exception:
            logging.exception("")
            st.error(f"Error while deleting item {item_id}")


st.title("🔧 Instruments")
st.subheader("Instrument Details")

with get_session() as session, session.begin():

    instruments = instruments_repo.get_all_instruments(session)

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
            or search_term in (inst.name_long or "").lower()
        ]
        st.session_state.instrument_id = None  # clear session
    elif st.session_state.instrument_id:
        filtered_instruments = [
            inst for inst in instruments
            if inst.id == st.session_state.instrument_id
        ]
    else:
        filtered_instruments = []

    if not filtered_instruments:
        st.info("No instruments found for the current search")
        st.stop()


    for inst in filtered_instruments:

        with st.container(border=True):
            
            # --- Row: Name and Ticker ---
            st.subheader(inst.name)

            # --- Row: Long name ---
            if inst.name_long:
                stripped = inst.name_long.strip()
                st.markdown(f"**{stripped}**")

            # --- Row: ISIN and Ticker ---
            col1, col2, col3 = st.columns([2,1,3])
            if inst.isin:
                col1.write(f"**ISIN:** [{inst.isin}](https://www.justetf.com/en/etf-profile.html?isin={inst.isin})")
            if inst.ticker:
                col2.markdown(f"**Ticker**: [{inst.ticker}](https://finance.yahoo.com/quote/{inst.ticker})")

            # --- Row: Currency and Category ---
            col1, col2, col3 = st.columns([2,1,3])
            if inst.currency:
                col1.write(f"**Currency:** {inst.currency or '-'}")
            if inst.ticker:
                col2.markdown(f"**Category**: {inst.category}")

            # --- Row: Description ---
            if inst.description:
                st.write(inst.description)

            # --- Row: empty ---
            st.write(" ")

            # --- Row: Button bar ---
            col1, col2, col3 = st.columns([6, 1, 1])
            with col2:
                if st.button("✏️ Edit", key=f"edit_{inst.id}"):
                    st.session_state["instrument_id"] = inst.id
                    st.switch_page("pages/instruments_edit.py")

            with col3:
                if st.button("🗑️ Delete", key=f"delete_{inst.id}"):
                    confirm_delete_dialog(f"Are you sure you want to delete instrument {inst.id} ?", inst.id, delete_instrument)

            # --- Related trades ---
            st.divider()
            st.write("Trades:")
            if inst.trades:
                inst_trades = [{
                    "Account": trade.account.name,
                    "Type": "📥 Buy" if trade.type.lower() == "buy" else "📤 Sell" if trade.type.lower() == "sell" else trade.type,
                    "Date": to_local(trade.date),
                    "Qty": trade.quantity,
                    "Price": read_from_db(trade.price)
                } for trade in inst.trades]
                st.dataframe(data=pd.DataFrame(inst_trades), hide_index=True)
            else:
                st.info("No trades available")
            cols = st.columns([5,1])
            with cols[1]:
                if st.button("Add new trade", key=f"add_trade_button_{inst.id}"):
                    st.session_state.trade_id = None
                    st.session_state.instrument_id = inst.id
                    st.switch_page("pages/trades_edit.py")