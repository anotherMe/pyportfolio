
import pandas as pd
import streamlit as st
from lib.database import read_from_db, get_session
from lib.models import Instrument, Position, Transaction
from lib.models import Trade
from lib.repo import trades_repository, transactions_repository
from lib.utils import confirm_delete_dialog
from service import positions_service as service
from service.utils import format_currency, format_currency_color, to_local

from logging_config import setup_logger
log = setup_logger(__name__)

log.debug("Running Positions details page...")


def delete_trade(item_id):
    with get_session() as session, session.begin():
        try:
            trades_repository.delete_trade(session, item_id)
            session.commit()
        except Exception:
            log.exception("")
            st.error(f"Error while deleting item {item_id}")

def delete_transaction(item_id):
    with get_session() as session, session.begin():
        try:
            transactions_repository.delete_transaction(session, item_id)
            session.commit()
        except Exception:
            log.exception("")
            st.error(f"Error while deleting item {item_id}")


if "position_id" not in st.session_state:
    st.session_state.position_id = None
if "trade_id" not in st.session_state:
    st.session_state.trade_id = None
if "transaction_id" not in st.session_state:
    st.session_state.transaction_id = None

st.title("Positions")

if not st.session_state.position_id:
    st.write("No Position selected")
    if st.button("Back to list"):
        st.switch_page("pages/positions_list.py")
    st.stop()

st.subheader(f"Position {st.session_state.position_id} details")

with get_session() as session, session.begin():

    position = session.get(Position, st.session_state.position_id)
    inst = session.get(Instrument, position.instrument_id)

    with st.container(border=True):
        
        # --- Row: Instrument details ---

        with st.container(horizontal=True):
            st.subheader(inst.name)
            if st.button("Edit position"):
                st.session_state.position_id = position.id
                st.session_state.instrument_id = position.instrument.id
                st.switch_page("pages/positions_edit.py")

        if inst.name_long:
            stripped = inst.name_long.strip()
            st.markdown(f"**{stripped}**")

        col1, col2, col3 = st.columns([2,1,3])

        if inst.isin:
            col1.write(f"**ISIN:** [{inst.isin}](https://www.justetf.com/en/etf-profile.html?isin={inst.isin})")
        if inst.ticker:
            col2.markdown(f"**Ticker**: [{inst.ticker}](https://finance.yahoo.com/quote/{inst.ticker})")
        if inst.currency:
            col1.write(f"**Currency:** {inst.currency.name} ({inst.currency.symbol})")
        col2.markdown(f"**Category**: {inst.category}")

        currency = inst.currency  # Currency enum member — sourced from CurrencyType


        if inst.description:
            st.write(inst.description)

        # -----------------------------------------------------------------------------
        # --- Row: Position details ---
        # -----------------------------------------------------------------------------

        st.divider()
        
        position_summary = service.get_position_summary(session, position)
        col1, col2 = st.columns([1,1])
        # st.write(f"**Position ID:** {position_summary.position_id}")
        col1.write(f"**Account:** {position.account.name}")
        col1.write(f"**Opening date:** {to_local(position_summary.opening_date)}")
        col1.write(f"**Closing date:** {to_local(position_summary.closing_date) if position_summary.closing_date else 'N/A'}")
        col1.write(f"**Remaining quantity:** {position_summary.remaining_quantity}")
        # st.write(f"**Average buy price:** {format_currency(position_summary.avg_buy_price, Currency.from_code(inst.currency).symbol)}")
        col1.write(f"**Total invested:** {format_currency(position_summary.total_invested, currency.symbol)}")

        col2.write(f"**Realized PnL:** {format_currency_color(position_summary.realized_pnl, currency.symbol)}")
        col2.write(f"**Transactions amount:** {format_currency_color(position_summary.transactions_amount, currency.symbol)}")
        col2.write(f"**Latest market price:** {format_currency(position_summary.latest_price, currency.symbol)} ( as of {to_local(position_summary.latest_price_date) if position_summary.latest_price_date else 'N/A'} )")
        col2.write(f"**Unrealized PnL:** {format_currency_color(position_summary.unrealized_pnl, currency.symbol)}")
        col2.write(f"**Total PnL:** {format_currency_color(position_summary.pnl, currency.symbol)}")
        pnl_percent = position_summary.pnl_percent * 100 if position_summary.pnl_percent is not None else None
        col2.write(f"**Total PnL:** {pnl_percent:.2f} %" if pnl_percent is not None else "N/A")


        # -----------------------------------------------------------------------------
        # --- Trades list ---
        # -----------------------------------------------------------------------------

        st.divider()
        st.subheader("Trades:")

        if position.trades:

            position_trades = [{
                "Date": to_local(trade.date),
                # "Type": "📥 Buy" if trade.type.lower() == "buy" else "📤 Sell" if trade.type.lower() == "sell" else trade.type,
                "Type": "➕ BUY" if trade.type.lower() == "buy" else "➖ SELL",
                "Qty": trade.quantity,
                "Price": format_currency(read_from_db(trade.price), currency.symbol),
                "Total": format_currency(read_from_db(trade.price) * trade.quantity, currency.symbol)
            } for trade in position.trades]
            trades_dataframe = st.dataframe(
                data=pd.DataFrame(position_trades), 
                hide_index=True,
                on_select="rerun", 
                selection_mode="single-row"
            )

            if trades_dataframe["selection"]["rows"]:
                dataframe_index = trades_dataframe["selection"]["rows"][0]
                selected_trade: Trade = position.trades[dataframe_index]
                with st.container(horizontal=True):
                    # st.space("stretch")
                    if st.button("Detail", key="trade_detail_btn"):
                        st.session_state.trade_id = selected_trade.id
                        st.switch_page("pages/trades_detail.py")
                    if st.button("Edit", type="secondary", key="trade_edit_btn"):
                        st.session_state.trade_id = selected_trade.id
                        st.switch_page("pages/trades_edit.py")
                    if st.button("Delete", type="primary", key="trade_delete_btn"):
                        confirm_delete_dialog(f"Are you sure you want to delete trade {selected_trade.id} ?", selected_trade.id, delete_trade)

            # (col1, col2) = st.columns([5,2])
            # with col2:
            #     st.space("stretch")
            #     st.write(f"##### Remaining quantity: {position_summary.remaining_quantity}")

        else:
            st.info("No trades available")

        cols = st.columns([5,1])
        with cols[1]:
            if st.button("Add new trade", key=f"add_trade_button_{position.id}"):
                st.session_state.trade_id = None
                st.session_state.position_id = position.id
                st.switch_page("pages/trades_edit.py")

        # -----------------------------------------------------------------------------
        # --- Transactions list ---
        # -----------------------------------------------------------------------------

        st.divider()
        st.write("Transactions:")
        if position.transactions:

            position_transactions = [{
                "Type": txn.type,
                "Amount": f"{read_from_db(txn.amount):.2f} {currency.symbol}",
                "Date": to_local(txn.date)
            } for txn in position.transactions]

            transactions_dataframe = st.dataframe(
                data=pd.DataFrame(position_transactions),
                hide_index=True,
                on_select="rerun", 
                selection_mode="single-row"
            )

            if transactions_dataframe["selection"]["rows"]:
                dataframe_index = transactions_dataframe["selection"]["rows"][0]
                selected_transaction: Transaction = position.transactions[dataframe_index]
                with st.container(horizontal=True):
                    # st.space("stretch")
                    if st.button("Detail", key="txn_detail_btn"):
                        st.session_state.transaction_id = selected_transaction.id
                        st.switch_page("pages/transactions_detail.py")
                    if st.button("Edit", type="secondary", key="txn_edit_btn"):
                        st.session_state.transaction_id = selected_transaction.id
                        st.switch_page("pages/transactions_edit.py")
                    if st.button("Delete", type="primary", key="txn_delete_btn"):
                        confirm_delete_dialog(f"Are you sure you want to delete transaction {selected_transaction.id} ?", selected_transaction.id, delete_transaction)

        else:
            st.info("No transactions available")


        cols = st.columns([5,1])
        with cols[1]:
            if st.button("Add new transaction", key=f"add_trans_btn_{position.id}"):
                st.session_state.position_id = position.id
                st.switch_page("pages/transactions_edit.py")



    with st.container(horizontal=True):
        st.space("stretch")
        if st.button("Back to list"):
            st.switch_page("pages/positions_list.py")