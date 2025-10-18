
from datetime import datetime
import streamlit as st
from lib.database import from_cents, get_session
from lib.trades_repository import add_trade
from lib.models import Instrument, Trade
from datetime import date


print("Running trades page...")

st.title("💼 Trades")

if 'trade_id' not in st.session_state:
    st.session_state.trade_id = None


with get_session() as session:

    if st.session_state.trade_id is None:
    
        st.subheader("Add New Trade")

        with st.form("add_trade"):

            trade = Trade()

            instruments = session.query(Instrument).all()
            instrument_map = {inst.name: inst for inst in instruments}
            selected_instrument = st.selectbox(
                "Instrument",
                list(instrument_map.keys())
            )
            trade_type = st.selectbox(
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
                    session.add(trade)
                    st.session_state.trade_id = None
                    st.success("✅ Instrument saved successfully!")

    else:

        instruments = session.query(Instrument).all()
        instrument_map = {inst.name: inst for inst in instruments}
        trades = session.query(Trade).join(Trade.instrument).order_by(Trade.date).all()
        latest_trades = session.query(Trade).join(Trade.instrument).order_by(Trade.date.desc()).limit(10).all()

        with st.container():
            st.subheader("Edit Trades")

            current_trade = next((trade for trade in trades if trade.id == st.session_state.trade_id), None)

            with st.form("edit_trade"):
                selected_instrument = st.selectbox(
                    "Instrument",
                    list(instrument_map.keys()),
                    index=list(instrument_map.keys()).index(current_trade.instrument.name), 
                    disabled=False
                )
                trade_type = st.selectbox(
                    "Type",
                    ["buy", "sell"],
                    index=["buy", "sell"].index(current_trade.type) if current_trade and current_trade.type in ["buy", "sell"] else 0
                )
                qty = st.number_input("Quantity", min_value=1, step=1, value=getattr(current_trade, "quantity", 1))
                price = st.number_input("Price (€)", min_value=0.0, step=0.01, value=from_cents(getattr(current_trade, "price", 1)))
                date = st.date_input("Payment date", value=getattr(current_trade, "date", datetime.today()))
                time = st.time_input("Payment time", value=getattr(current_trade, "date", datetime.now()).time())
                notes = st.text_area("Notes", value="")
                submitted = st.form_submit_button("Save")

            col1, col2 = st.columns(2)
            with col1:
                if submitted:
                    try:
                        add_trade(session, current_trade.instrument, trade_type, qty, price, notes)
                        st.success(f"Trade added for {current_trade.instrument.name}")
                        st.session_state.show_editor = False
                        st.session_state.trade_id = None
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error adding trade: {e}")
                        
                with col2:
                    cancel = st.button("❌ Cancel")

            if cancel:
                st.session_state.show_editor = False
                st.session_state.trade_id = None
                st.rerun()
