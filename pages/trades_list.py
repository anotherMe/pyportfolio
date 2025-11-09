
import logging
import streamlit as st
from lib.models import Trade
from lib.repo.accounts_repository import get_account_by_name, get_all_accounts
from lib.database import read_from_db, get_session
from lib.repo.instruments_repository import get_all_instruments
import pandas as pd

from lib.utils import confirm_delete_dialog
from service.utils import account_selector, to_local
import lib.repo.trades_repository as trades_repo

from logging_config import setup_logger
log = setup_logger(__name__)

log.debug("Running trades page...")

st.title("💼 Trades")

if 'show_editor' not in st.session_state:
    st.session_state.show_editor = False
if 'trade_id' not in st.session_state:
    st.session_state.trade_id = None

def delete_trade(item_id):
    with get_session() as session, session.begin():
        try:
            trades_repo.delete_trade(session, item_id)
            session.commit()
        except Exception:
            logging.exception("")
            st.error(f"Error while deleting item {item_id}")

with get_session() as session:

    # --- Account selector ---
    accounts = get_all_accounts(session)
    account_selector(accounts) # Show sidebar account selector
    current_account = get_account_by_name(session, st.session_state.account)

    # --- Fetch data ---
    instruments = get_all_instruments(session)
    instrument_map = {inst.name: inst for inst in instruments}
    trades = trades_repo.get_all_trades(session, current_account)
    # latest_trades = session.query(Trade).join(Trade.instrument).order_by(Trade.date.desc()).limit(10).all()

    if not trades:
        st.info("No trades found")
        st.stop()

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

    
    # --------------------------------------------------------------------------------------------------------------

    st.subheader("Trades")
    
    if filtered_trades:
        
        latest_trade_details = [{
            "trade_id": t.id,
            "Instrument": t.instrument.name,
            "ISIN": t.instrument.isin,
            "Date": to_local(t.date),
            "Type": "➕ BUY" if t.type.lower() == "buy" else "➖ SELL",
            "Quantity": t.quantity,
            "Price": f"{read_from_db(t.price)}"
        } for t in filtered_trades]
        
        df_latest = pd.DataFrame(latest_trade_details)

        my_column_config = {

            "trade_id": None,
            "Instrument": "Instrument",
            "ISIN": "ISIN",
            # "ISIN": st.column_config.LinkColumn(
            #     help="Look up ISIN on JustETF site",
            #     display_text=r"[?&]isin=([^&#]+)"
            # ),
            "Date": "Date",
            "Type": "Type",
            "Quantity": "Quantity",
            "Price": "Price"
        }

        the_dataframe = st.dataframe(
            data=df_latest,
            column_config=my_column_config, 
            hide_index=True, 
            on_select="rerun", 
            selection_mode="single-row")

    else:
        st.info("No trades available for the current search")


    if the_dataframe["selection"]["rows"]:
        dataframe_index = the_dataframe["selection"]["rows"][0]
        trade: Trade = filtered_trades[dataframe_index]
        with st.container(horizontal=True):
            st.space("stretch")
            if st.button("Show details"):
                st.session_state.trade_id = trade.id
                st.switch_page("pages/trades_edit.py")
            if st.button("Delete", type="primary"):
                confirm_delete_dialog(f"Are you sure you want to delete trade {trade.id} ?", trade.id, delete_trade)