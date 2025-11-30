
from datetime import datetime
from datetime import date

import streamlit as st

from lib.repo.accounts_repository import get_all_accounts
from lib.database import read_from_db, get_session, write_to_db
from lib.repo.instruments_repository import get_all_instruments
from lib.models import Instrument, Trade, Transaction
from lib.settings_manager import get_timezone

from logging_config import setup_logger
log = setup_logger(__name__)

print("Running trades page...")

st.title("💼 Trades")

if 'trade_id' not in st.session_state:
    st.session_state.trade_id = None
if 'instrument_id' not in st.session_state:
    st.session_state.instrument_id = None


with get_session() as session, session.begin():

    accounts = get_all_accounts(session)
    accounts_map = {account.name: account for account in accounts}
    instruments = get_all_instruments(session)
    instrument_map = {inst.name: inst for inst in instruments}

    if st.session_state.trade_id is None:
    
        st.subheader("Add New Trade")

        with st.form("add_trade"):

            # if an instrument has been set from instrument_detail.py
            selected_instrument_index = None
            if st.session_state.instrument_id:
                work_on_instrument = session.get(Instrument, st.session_state.instrument_id)
                selected_instrument_index = list(instrument_map.keys()).index(work_on_instrument.name)

            trade = Trade()
            selected_account = st.selectbox(
                "Account",
                list(accounts_map.keys())
            )
            selected_instrument = st.selectbox(
                "Instrument",
                list(instrument_map.keys()),
                index=selected_instrument_index
            )
            selected_type = st.selectbox(
                "Type",
                ["buy", "sell"]
            )
            trade_quantity = st.number_input("Quantity", min_value=1, step=1, value=1)
            trade_price = st.number_input("Price (€)", min_value=0.0, value=1.0)
            trade_fee = st.number_input("Fee (€)", min_value=0.0, value=0.0)
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
                    # TODO: add try / except here
                    instrument_id = instrument_map.get(selected_instrument).id
                    trade.account_id = accounts_map.get(selected_account).id
                    trade.instrument_id = instrument_id
                    trade.date = datetime.combine(trade_date, trade_time).replace(tzinfo=get_timezone())
                    trade.quantity = trade_quantity
                    trade.price = write_to_db(trade_price)
                    trade.type = selected_type
                    session.add(trade)
                    # session.flush()
                    if trade_fee > 0:
                        fee_transaction = Transaction()
                        fee_transaction.account_id = trade.account_id
                        fee_transaction.trade_id = trade.id
                        fee_transaction.date = trade.date
                        fee_transaction.type = 'fee'
                        fee_transaction.amount = write_to_db(trade_fee)
                        fee_transaction.description = f"Fee for {trade.type}ing {trade.quantity} of {selected_instrument}"
                        session.add(fee_transaction)
                    st.session_state.trade_id = None
                    st.session_state.instrument_id = instrument_id
                    st.success("✅ Trade saved successfully!")

    else:

        with st.container():

            trade = session.get(Trade, st.session_state.trade_id)

            st.subheader("Edit Trade")
            with st.form("edit_trade"):

                selected_account = st.selectbox(
                    "Account",
                    list(accounts_map.keys()),
                    index=list(accounts_map.keys()).index(trade.account.name), 
                )
                selected_instrument = st.selectbox(
                    "Instrument",
                    list(instrument_map.keys()),
                    index=list(instrument_map.keys()).index(trade.instrument.name)
                )
                selected_type = st.selectbox(
                    "Type",
                    ["buy", "sell"],
                    index=["buy", "sell"].index(trade.type) if trade and trade.type in ["buy", "sell"] else 0
                )
                qty = st.number_input("Quantity", min_value=1, step=1, value=getattr(trade, "quantity", 1))
                price = st.number_input("Price (€)", min_value=0.0, value=read_from_db(getattr(trade, "price", 1)))
                trade_date = st.date_input("Date", value=getattr(trade, "date", datetime.today()))
                trade_time = st.time_input("Time", value=getattr(trade, "date", datetime.now()).time())
                notes = st.text_area("Notes", value=getattr(trade, "description", ""))

                col1, col2 = st.columns([9,1])
                with col2:
                    submitted = st.form_submit_button("Save")

                if submitted:
                    try:
                        account = accounts_map.get(selected_account)
                        instrument_id = instrument_map.get(selected_instrument)

                        trade.account_id = account.id
                        trade.instrument_id = instrument_id.id
                        trade.date = datetime.combine(trade_date, trade_time).replace(tzinfo=get_timezone())
                        trade.type = selected_type
                        trade.quantity = qty
                        trade.price = write_to_db(price)
                        trade.description = notes
                        session.add(trade)
                        
                        st.success("Trade updated")
                        st.session_state.trade_id = trade.id
                        st.session_state.instrument_id = instrument_id.id

                    except Exception as e:
                        st.error(f"Error updating trade: {e}")

    col1, col2 = st.columns([5,1])
    with col2:
        if st.button("⬅️ Back to list"):
            st.switch_page("pages/trades_list.py")