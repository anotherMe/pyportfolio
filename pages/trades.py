
from datetime import datetime
import streamlit as st
from lib.database import from_cents, get_session
from lib.enums import PageAction
from lib.trades_repository import add_trade
from lib.models import Instrument, Trade
import pandas as pd

print("Running trades page...")

st.title("💼 Trades")

if 'show_editor' not in st.session_state:
    st.session_state.show_editor = False
if 'trade_id' not in st.session_state:
    st.session_state.trade_id = None

with get_session() as session:

    # --- Fetch data ---
    instruments = session.query(Instrument).all()
    instrument_map = {inst.name: inst for inst in instruments}
    trades = session.query(Trade).join(Trade.instrument).order_by(Trade.date).all()
    latest_trades = session.query(Trade).join(Trade.instrument).order_by(Trade.date.desc()).limit(10).all()


    # --- Page layout ---
    tab1, tab2 = st.tabs(["Latest", "Details"])

    with tab1:
        st.subheader("Latest Trades")
        
        if latest_trades:
            latest_trade_details = [{
                "Instrument": t.instrument.name,
                "ISIN": t.instrument.isin,
                "Date": t.date.strftime("%Y-%m-%d %H:%M"),
                "Type": t.type,
                "Quantity": t.quantity,
                "Price (€)": f"{t.price / 100:.2f}"
            } for t in latest_trades]
            df_latest = pd.DataFrame(latest_trade_details)
            st.dataframe(data=df_latest, hide_index=True)
        else:
            st.info("No trades available.")
        

    with tab2:

        st.subheader("Trade Details")

        # --- Search input ---
        search_term = st.text_input("🔍 Search by Instrument ISIN, Ticker, or Name").strip().lower()
        if search_term:
            filtered_trades = [
                trade for trade in trades
                if search_term in (trade.instrument.isin or "").lower()
                or search_term in (trade.instrument.ticker or "").lower()
                or search_term in (trade.instrument.name or "").lower()
            ]
        else:
            filtered_trades = trades

        st.divider()

        # --- Edit trade section ---

        if st.session_state.show_editor:
            with st.container():
                st.subheader("Edit Trades")

                current_trade = next((trade for trade in trades if trade.id == st.session_state.trade_id), None)

                with st.form("add_trade"):
                    selected_instrument = st.selectbox(
                        "Instrument",
                        list(instrument_map.keys()),
                        index=list(instrument_map.keys()).index(current_trade.instrument.name), 
                        disabled=True
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
                    # fees = st.number_input("Fees (€)", min_value=0.0, step=0.01, value=getattr(current_trade, "fees", 0.0))
                    # tax_rate = st.number_input("Tax Rate (%)", min_value=0.0, max_value=100.0, step=0.1, value=getattr(current_trade, "tax_rate", 26.0))
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

            st.divider()
        
        else:
            
            if filtered_trades:
                for trade in filtered_trades:
                    with st.container(border=True):

                        col1, col2, col3 = st.columns([1,1,1])
                        col1.write(f"Instrument: {trade.instrument.name}")
                        col2.write(f"ISIN: {trade.instrument.isin}")
                        col3.write(f"Date: {trade.date.strftime('%Y-%m-%d %H:%M')}")
                        
                        col1, col2, col3 = st.columns([1,1,1])
                        col1.write(trade.type)
                        col2.write(trade.quantity)
                        col3.write(f"{trade.price / 100:.2f} €")

                        col1, col2, col3, col4 = st.columns([5,1,2,1])
                        with col2:
                            if st.button("✏️ Edit", key=f"edit_{trade.id}"):
                                st.session_state.trade_id = trade.id
                                st.session_state.show_editor = True
                                st.rerun()
                        with col3:
                            if st.button("➕ Add transaction", key=f"add_transaction_{trade.id}"):
                                st.session_state.trade_id = trade.id
                                st.session_state.action = PageAction.ADD_TRANSACTION.value
                                st.switch_page("pages/transactions.py")
                        with col4:
                            if st.button("🗑️ Delete", key=f"delete_{trade.id}"):
                                st.warning("Delete functionality is not implemented yet.")
                                # session.delete(trade)
                                # st.success("Trade deleted.")

                        if trade.transactions:                        
                            st.divider()
                            st.write("Related Transactions:")
                            if trade.transactions:
                                txn_details = [{
                                    "Type": txn.type,
                                    "Amount (€)": f"{from_cents(txn.amount):.2f}",
                                    "Date": txn.date.strftime('%Y-%m-%d')
                                } for txn in trade.transactions]
                                st.dataframe(pd.DataFrame(txn_details))
            else:
                st.info("No trades available.")
                        