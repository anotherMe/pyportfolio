
from narwhals import col
import pandas as pd
import streamlit as st
from lib.database import read_from_db, get_session
from lib.enums import Currency
from lib.models import Instrument, Position
from lib.utils import confirm_delete_dialog
from service import positions_service as service
from service.utils import format_currency, format_currency_color, to_local

from logging_config import setup_logger
log = setup_logger(__name__)

log.debug("Running Positions details page...")

if "position_id" not in st.session_state:
    st.session_state.position_id = None


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

        st.subheader(inst.name)

        if inst.name_long:
            stripped = inst.name_long.strip()
            st.markdown(f"**{stripped}**")

        col1, col2, col3 = st.columns([2,1,3])

        if inst.isin:
            col1.write(f"**ISIN:** [{inst.isin}](https://www.justetf.com/en/etf-profile.html?isin={inst.isin})")
        if inst.ticker:
            col2.markdown(f"**Ticker**: [{inst.ticker}](https://finance.yahoo.com/quote/{inst.ticker})")
        if inst.currency:
            col1.write(f"**Currency:** {inst.currency or '-'}")
        col2.markdown(f"**Category**: {inst.category}")


        if inst.description:
            st.write(inst.description)

        # --- Row: Position details ---

        st.divider()
        
        position_summary = service.get_position_summary(session, position)
        col1, col2 = st.columns([1,1])
        # st.write(f"**Position ID:** {position_summary.position_id}")
        col1.write(f"**Account:** {position.account.name}")
        col1.write(f"**Opening date:** {to_local(position_summary.opening_date)}")
        col1.write(f"**Closing date:** {to_local(position_summary.closing_date) if position_summary.closing_date else 'N/A'}")
        col1.write(f"**Remaining quantity:** {position_summary.remaining_quantity}")
        # st.write(f"**Average buy price:** {format_currency(position_summary.avg_buy_price, Currency.from_code(inst.currency).symbol)}")
        col1.write(f"**Total buy cost:** {format_currency(position_summary.total_buy, Currency.from_code(inst.currency).symbol)}")

        col2.write(f"**Realized PnL:** {format_currency_color(position_summary.realized_pnl, Currency.from_code(inst.currency).symbol)}")
        col2.write(f"**Transactions amount:** {format_currency_color(position_summary.transactions_amount, Currency.from_code(inst.currency).symbol)}")
        col2.write(f"**Latest market price:** {format_currency(position_summary.latest_price, Currency.from_code(inst.currency).symbol)} ( as of {to_local(position_summary.latest_price_date) if position_summary.latest_price_date else 'N/A'} )")
        col2.write(f"**Unrealized PnL:** {format_currency_color(position_summary.unrealized_pnl, Currency.from_code(inst.currency).symbol)}")
        col2.write(f"**Total PnL:** {format_currency_color(position_summary.pnl, Currency.from_code(inst.currency).symbol)}")
        pnl_percent = position_summary.pnl_percent * 100 if position_summary.pnl_percent is not None else None
        col2.write(f"**Total PnL:** {pnl_percent:.2f} %" if pnl_percent is not None else "N/A")

        # --- Related Trades ---

        st.divider()
        st.write("Trades:")
        if position.trades:

            position_trades = [{
                "Account": trade.account.name,
                "Type": "📥 Buy" if trade.type.lower() == "buy" else "📤 Sell" if trade.type.lower() == "sell" else trade.type,
                "Date": to_local(trade.date),
                "Qty": trade.quantity,
                "Price": format_currency(read_from_db(trade.price), Currency.from_code(inst.currency).symbol),
                "Total": format_currency(read_from_db(trade.price) * trade.quantity, Currency.from_code(inst.currency).symbol)
            } for trade in position.trades]
            st.dataframe(data=pd.DataFrame(position_trades), hide_index=True)

            # (col1, col2) = st.columns([5,2])
            # with col2:
            #     st.space("stretch")
            #     st.write(f"##### Remaining quantity: {position_summary.remaining_quantity}")

        else:
            st.info("No trades available")

        cols = st.columns([5,1])
        with cols[1]:
            if st.button("Add new trade", key=f"add_trade_button_{inst.id}"):
                st.session_state.trade_id = None
                st.session_state.position_id = inst.id
                st.switch_page("pages/trades_edit.py")


        # --- Related Transactions ---

        st.divider()
        st.write("Transactions:")
        if position.transactions:                        
            txn_detail = [{
                "Type": txn.type,
                "Amount (€)": f"{read_from_db(txn.amount):.2f}",
                "Date": to_local(txn.date)
            } for txn in position.transactions]
            st.dataframe(pd.DataFrame(txn_detail))
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