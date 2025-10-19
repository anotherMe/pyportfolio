
from datetime import datetime
from datetime import date

import streamlit as st

from lib.accounts_repository import get_all_accounts
from lib.database import from_cents, get_session
from lib.instruments_repository import get_all_instruments
from lib.trades_repository import add_trade
from lib.models import Trade


print("Running trades page...")

st.title("💼 Trades")

if 'trade_id' not in st.session_state:
    st.session_state.trade_id = None


with get_session() as session:

    accounts = get_all_accounts(session)
    accounts_map = {account.name: account for account in accounts}
    instruments = get_all_instruments(session)
    instrument_map = {inst.name: inst for inst in instruments}

    if st.session_state.trade_id is None:
    
        st.subheader("Add New Trade")

        with st.form("add_trade"):

            trade = Trade()
            selected_account = st.selectbox(
                "Account",
                list(accounts_map.keys())
            )
            selected_instrument = st.selectbox(
                "Instrument",
                list(instrument_map.keys())
            )
            selected_type = st.selectbox(
                "Type",
                ["buy", "sell"]
            )
            trade.quantity = st.number_input("Quantity", min_value=1, step=1, value=1)
            trade.price = st.number_input("Price (€)", min_value=0.0, step=0.01, value=1.0)
            trade_date = st.date_input("Transaction date", value=date.today())
            trade_time = st.time_input("Transaction time", value="now", step=60)
            notes = st.text_area("Notes", value="")

            col1, col2 = st.columns([7,1])
            with col2:
                save = st.form_submit_button("💾 Save")

            if save:
                if not selected_instrument:
                    st.warning("Instrument must be selected.")
                else:
                    trade.account_id = accounts_map.get(selected_account).id
                    trade.instrument_id = instrument_map.get(selected_instrument).id
                    trade.type = selected_type
                    session.add(trade)
                    st.session_state.trade_id = None
                    st.success("✅ Trade saved successfully!")

    else:

        with st.container():

            current_trade = session.get(Trade, st.session_state.trade_id)

            st.subheader("Edit Trade")
            with st.form("edit_trade"):

                selected_account = st.selectbox(
                    "Account",
                    list(accounts_map.keys()),
                    index=list(accounts_map.keys()).index(current_trade.account.name), 
                )
                selected_instrument = st.selectbox(
                    "Instrument",
                    list(instrument_map.keys()),
                    index=list(instrument_map.keys()).index(current_trade.instrument.name)
                )
                selected_type = st.selectbox(
                    "Type",
                    ["buy", "sell"],
                    index=["buy", "sell"].index(current_trade.type) if current_trade and current_trade.type in ["buy", "sell"] else 0
                )
                qty = st.number_input("Quantity", min_value=1, step=1, value=getattr(current_trade, "quantity", 1))
                price = st.number_input("Price (€)", min_value=0.0, step=0.01, value=from_cents(getattr(current_trade, "price", 1)))
                date = st.date_input("Payment date", value=getattr(current_trade, "date", datetime.today()))
                time = st.time_input("Payment time", value=getattr(current_trade, "date", datetime.now()).time())
                notes = st.text_area("Notes", value="")

                col1, col2 = st.columns([9,1])
                with col2:
                    submitted = st.form_submit_button("Save")
                    if submitted:
                        try:
                            account = accounts_map.get(selected_account)
                            instrument = instrument_map.get(selected_instrument)
                            add_trade(session, account, instrument, selected_type, qty, price, notes)
                            st.success("Trade added")
                            st.session_state.show_editor = False
                            st.session_state.trade_id = None
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error adding trade: {e}")

    col1, col2 = st.columns([5,1])
    with col2:
        if st.button("⬅️ Back to details"):
            st.session_state.show_editor = False
            st.session_state.trade_id = None
            st.switch_page("pages/trades_details.py")