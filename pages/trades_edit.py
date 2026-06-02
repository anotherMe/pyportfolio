
from datetime import datetime
from datetime import date

import streamlit as st

from lib.database import get_session
from lib.enums import TradeType
from lib.settings_manager import get_timezone
from service.positions_service import PositionsService
from service.trades_service import TradesService
from service.dtos import TradeCreateDTO

from logging_config import setup_logger
log = setup_logger(__name__)

log.debug("Running trades edit page...")

st.title("Trades")

if 'trade_id' not in st.session_state:
    st.session_state.trade_id = None
if 'position_id' not in st.session_state:
    st.session_state.position_id = None

trades_service = TradesService()
positions_service = PositionsService()


with get_session() as session:

    positions = positions_service.get_all_basic(session)
    positions_map = {pos.id: pos for pos in positions}

    if st.session_state.trade_id is None:

        st.subheader("Add New Trade")

        with st.form("add_trade"):

            selected_position_index = None
            currency_symbol = ""
            if st.session_state.position_id and st.session_state.position_id in positions_map:
                work_pos = positions_map[st.session_state.position_id]
                selected_position_index = list(positions_map.keys()).index(work_pos.id)
                currency_symbol = work_pos.instrument_symbol

            selected_position_id = st.selectbox(
                "Position",
                list(positions_map.keys()),
                index=selected_position_index,
                format_func=lambda pid: f"{positions_map[pid].instrument_name} ({positions_map[pid].account_name})" if pid in positions_map else str(pid),
                disabled=True,
            )
            selected_type = st.selectbox(
                "Type",
                options=list(TradeType),
                format_func=lambda t: t.value.upper(),
            )
            trade_quantity = st.number_input("Quantity", min_value=1, step=1, value=1)
            trade_price = st.number_input(f"Price{' (' + currency_symbol + ')' if currency_symbol else ''}", min_value=0.0, value=1.0)
            trade_fee = st.number_input(f"Fee{' (' + currency_symbol + ')' if currency_symbol else ''}", min_value=0.0, value=0.0)
            trade_date = st.date_input("Transaction date", value=date.today())
            trade_time = st.time_input("Transaction time", value="now", step=60)
            notes = st.text_area("Notes", value="")

            col1, col2 = st.columns([7, 1])
            with col2:
                save = st.form_submit_button("💾 Save")

            if save:
                if not selected_position_id:
                    st.warning("Position must be selected.")
                else:
                    try:
                        dto = TradeCreateDTO(
                            position_id=selected_position_id,
                            date=datetime.combine(trade_date, trade_time).replace(tzinfo=get_timezone()),
                            type=selected_type,
                            quantity=trade_quantity,
                            price=trade_price,
                            fee=trade_fee,
                            description=notes or None,
                        )
                        trades_service.create(session, dto)
                        st.session_state.trade_id = None
                        st.session_state.position_id = selected_position_id
                        st.success("✅ Trade saved successfully!")
                    except Exception as e:
                        log.exception("")
                        st.error(f"Error saving trade: {e}")

    else:

        trades = trades_service.get_all(session)
        trade = next((t for t in trades if t.id == st.session_state.trade_id), None)

        if trade is None:
            st.error("Trade not found.")
            st.stop()

        with st.container(horizontal=True):
            st.subheader(f"Editing Trade with ID: {trade.id}")
            if st.button("Clear selection"):
                st.session_state.trade_id = None
                st.session_state.position_id = None
                st.rerun()

        with st.form("edit_trade"):

            selected_position_id = st.selectbox(
                "Position",
                list(positions_map.keys()),
                index=list(positions_map.keys()).index(trade.position_id) if trade.position_id in positions_map else 0,
                format_func=lambda pid: f"{positions_map[pid].instrument_name} ({positions_map[pid].account_name})" if pid in positions_map else str(pid),
                disabled=True,
            )
            selected_type = st.selectbox(
                "Type",
                options=list(TradeType),
                format_func=lambda t: t.value.upper(),
                index=list(TradeType).index(trade.type),
            )
            qty = st.number_input("Quantity", min_value=1, step=1, value=trade.quantity)
            price = st.number_input(
                f"Price{' (' + trade.currency_symbol + ')' if trade.currency_symbol else ''}",
                min_value=0.0,
                value=trade.price,
            )
            trade_date = st.date_input("Date", value=trade.date)
            trade_time = st.time_input("Time", value=trade.date.time())
            notes = st.text_area("Notes", value=trade.description or "")

            with st.container(horizontal=True, horizontal_alignment="right"):
                submitted = st.form_submit_button("Save")

            if submitted:
                try:
                    dto = TradeCreateDTO(
                        position_id=selected_position_id,
                        date=datetime.combine(trade_date, trade_time).replace(tzinfo=get_timezone()),
                        type=selected_type,
                        quantity=qty,
                        price=price,
                        description=notes or None,
                    )
                    trades_service.update(session, trade.id, dto)
                    st.success("Trade updated")
                    st.session_state.position_id = selected_position_id
                except Exception as e:
                    log.exception("")
                    st.error(f"Error updating trade: {e}")

    with st.container(horizontal=True):
        st.space("stretch")
        if st.button("⬅️ Positions list"):
            st.session_state.trade_id = None
            st.session_state.position_id = None
            st.switch_page("pages/positions_list.py")
        if st.button("⬅️ Trades list"):
            st.session_state.trade_id = None
            st.session_state.position_id = None
            st.switch_page("pages/trades_list.py")
