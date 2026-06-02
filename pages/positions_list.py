
import pandas as pd
import streamlit as st
import datetime as dt
import plotly.graph_objects as go

from lib.database import get_session
from lib.utils import confirm_delete_dialog
from service.accounts_service import AccountsService
from service.instruments_service import InstrumentsService
from service.ohlcvs_service import OhlcvsService
from service.positions_service import PositionsService
from service.trades_service import TradesService
from service.transactions_service import TransactionsService
from service.utils import format_currency, format_currency_color, to_local


# --------------------------------------------------------------------------------
# -- utility functions

def format_and_style_positions(df):
    """Add formatted display columns and apply color styling with type icons."""

    # Pre-format monetary columns as "1,234.56 $" using the per-row instrument_symbol.
    # Done before Styler because format() callbacks receive a scalar with no row context.
    def fmt_money(series):
        return series.map(lambda v: f"{v:,.2f}") + " " + df["instrument_symbol"]

    df.insert(len(df.columns), "pnl_styled", fmt_money(df["pnl"]))
    df.insert(len(df.columns), "transactions_amount_styled", fmt_money(df["transactions_amount"]))
    df.insert(len(df.columns), "pnl_percent_styled", df["pnl_percent"])
    df.insert(5, "opening_date_styled", df["opening_date"])
    df.insert(len(df.columns), "closing_date_styled", df["closing_date"])

    def color_price(v):
        # v is a pre-formatted string like "1,234.56 $"; parse the numeric part
        try:
            numeric = float(str(v).split()[0].replace(",", ""))
        except (ValueError, IndexError):
            numeric = 0
        color = "green" if numeric > 0 else "red" if numeric < 0 else "gray"
        return f"color: {color}; font-weight: bold;"

    def format_percent(v):
        return f"{v*100:,.2f} %"

    def format_date(v):
        return "" if pd.isna(v) else dt.datetime.fromisoformat(v).strftime("%Y-%m-%d %H:%M:%S")

    # Apply styles — pnl_styled / transactions_amount_styled are already strings, pass through
    styled = (
        df.style
        .format({
            "pnl_styled": lambda v: v,
            "pnl_percent_styled": format_percent,
            "transactions_amount_styled": lambda v: v,
            "closing_date_styled": format_date,
            "opening_date_styled": format_date,
        })
        .map(color_price, subset=["pnl_styled", "pnl_percent_styled"])
    )

    return styled

def clear_search():
    st.session_state.search_term = ""

# --------------------------------------------------------------------------------
# -- Streamlit page

if "status_filter" not in st.session_state:
    st.session_state.status_filter = "all"

st.title("Current market positions")

options = {
    "Show all positions": "all",
    "Show open positions": "open",
    "Show closed positions": "closed"
}

selected_label = st.selectbox(
    "Select status:",
    options=list(options.keys())
)

st.session_state.status_filter = options[selected_label]


_accounts_service = AccountsService()
_positions_service = PositionsService()
_instruments_service = InstrumentsService()
_ohlcvs_service = OhlcvsService()
_trades_service = TradesService()
_transactions_service = TransactionsService()


def delete_trade(item_id):
    with get_session() as session:
        try:
            _trades_service.delete(session, item_id)
        except Exception:
            st.error(f"Error while deleting trade {item_id}")


def delete_transaction(item_id):
    with get_session() as session:
        try:
            _transactions_service.delete(session, item_id)
        except Exception:
            st.error(f"Error while deleting transaction {item_id}")

with get_session() as session:

    current_account = _accounts_service.get_by_name(session, st.session_state.account)
    account_id = current_account.id if current_account else 0

    include_closed = True
    include_open = True
    if st.session_state.status_filter == 'open':
        include_closed = False
    elif st.session_state.status_filter == 'closed':
        include_open = False

    positions_df = _positions_service.get_summary(session, account_id=account_id, include_closed=include_closed, 
                                                  include_open=include_open)

    if positions_df.empty:
        st.write("No positions found.")
        st.stop()

    # --- Filter positions by Instrument ---

    col1, col2 = st.columns([5, 1], vertical_alignment="bottom")
    with col1:
        # st.space("stretch")
        search_term = st.text_input("🔍 Search by Instrument ISIN, Ticker, or Name", key="search_term" ).strip().lower()
    with col2:
        st.button(label="", icon=":material/clear_all:", on_click=clear_search)

    if search_term:
        mask = (
            positions_df['instrument_name'].str.contains(search_term, na=False, case=False) |
            positions_df['instrument_isin'].str.contains(search_term, na=False, case=False) |
            positions_df['instrument_ticker'].str.contains(search_term, na=False, case=False)
        )

        filtered_positions_df = positions_df[mask]
    else:
        filtered_positions_df = positions_df

    st.space()

    # --- Show dataframe

    styled_positions = format_and_style_positions(filtered_positions_df)
    st_dataframe = st.dataframe(
        data=styled_positions,
        column_config={
            "position_id": st.column_config.NumberColumn("ID"),
            "opening_date": None,
            "opening_date_styled": "First buy on",
            "instrument_id": None,
            "instrument_name": "Instrument",
            "instrument_isin": None,
            "instrument_ticker": "Ticker",
            "instrument_currency": None,
            "instrument_symbol": None,
            "remaining_quantity": None,
            "remaining_cost_basis": None,
            "position_closed": "Remaining Qty",
            "avg_buy_price": None,
            # "total_invested": st.column_config.NumberColumn("Total buy cost", format="euro"),
            "total_invested": None,
            "closing_price": "Market price",
            "realized_pnl": None,
            "realized_pnl_percent": None,
            "latest_price": None,
            "latest_price_date": None,
            "unrealized_pnl": None,
            "unrealized_pnl_percent": None,
            "pnl": None,
            "pnl_styled": "PnL",
            "transactions_amount": None,
            # "transactions_amount_styled": st.column_config.NumberColumn("Transactions amount", format="euro"),
            "transactions_amount_styled": None,
            "pnl_percent": None,
            "pnl_percent_styled": st.column_config.NumberColumn("PnL %"),
            "closing_date": None,
            "closing_date_styled": None  # "Closed on"
        },
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row"
    )

    # --- Buttons --- 

    with st.container(horizontal=True, horizontal_alignment="right"):
        if st.button("➕ Add new", type="secondary"):
            st.session_state["position_id"] = None
            st.switch_page("pages/positions_edit.py")

    # --- Check if a row has been selected

    selected_position_id = None
    if st_dataframe["selection"]["rows"]:
        dataframe_index = st_dataframe["selection"]["rows"][0]
        selected_position_id = filtered_positions_df.iloc[dataframe_index].position_id.item()
        selected_instrument_id = filtered_positions_df.iloc[dataframe_index].instrument_id.item()

    if not selected_position_id:

        # --- Totals --- 

        total_invested_sum = filtered_positions_df["total_invested"].sum()
        total_pnl = (filtered_positions_df["pnl"]).sum()

        color = "green" if total_pnl > 0 else "red"
        st.markdown(
            f"<h3>Total buy: <span>{total_invested_sum:,.2f} €</span></h3>",
            unsafe_allow_html=True
        )
        st.markdown(
            f"<h3>Total PnL: <span style='color:{color}'>{total_pnl:,.2f} €</span></h3>",
            unsafe_allow_html=True
        )

        st.stop()

    # -- Position details ----------------------------------------------------------------------------------------------

    st.space()
    positions_basic = _positions_service.get_all_basic(session)
    position_basic = next((p for p in positions_basic if p.id == selected_position_id), None)

    if position_basic:
        instruments = _instruments_service.get_all(session)
        inst = next((i for i in instruments if i.id == position_basic.instrument_id), None)
        position_summary = _positions_service.get_position_summary(session, selected_position_id)
        currency_symbol = position_basic.instrument_symbol

        with st.container(border=True):

            # --- Instrument details -------------------------------------------------------------------------------

            st.subheader(position_basic.instrument_name)
            if inst and inst.name_long:
                st.markdown(f"**{inst.name_long.strip()}**")
            col1, col2, col3 = st.columns([2, 1, 3])
            if inst and inst.isin:
                col1.write(f"**ISIN:** [{inst.isin}](https://www.justetf.com/en/etf-profile.html?isin={inst.isin})")
            if inst and inst.ticker:
                col2.markdown(f"**Ticker**: [{inst.ticker}](https://finance.yahoo.com/quote/{inst.ticker})")
            if inst and inst.currency:
                col1.write(f"**Currency:** {inst.currency.name} ({inst.currency.symbol})")
            if inst and inst.dist_policy:
                col2.markdown(f"**Category**: {inst.dist_policy.value}")
            if inst and inst.description:
                st.write(inst.description)

            # --- Position summary ---------------------------------------------------------------------------------

            st.space()
            col1, col2 = st.columns([1, 1])
            col1.write(f"**Account:** {position_basic.account_name}")
            col1.write(f"**Opening date:** {to_local(position_summary.opening_date)}")
            col1.write(f"**Closing date:** {to_local(position_summary.closing_date) if position_summary.closing_date else 'N/A'}")
            col1.write(f"**Remaining quantity:** {position_summary.remaining_quantity}")
            col1.write(f"**Total invested:** {format_currency(position_summary.total_invested, currency_symbol)}")
            col2.write(f"**Realized PnL:** {format_currency_color(position_summary.realized_pnl, currency_symbol)}")
            col2.write(f"**Transactions amount:** {format_currency_color(position_summary.transactions_amount, currency_symbol)}")
            col2.write(f"**Latest market price:** {format_currency(position_summary.latest_price, currency_symbol)} ( as of {to_local(position_summary.latest_price_date) if position_summary.latest_price_date else 'N/A'} )")
            col2.write(f"**Unrealized PnL:** {format_currency_color(position_summary.unrealized_pnl, currency_symbol)}")
            col2.write(f"**Total PnL:** {format_currency_color(position_summary.pnl, currency_symbol)}")
            pnl_percent = position_summary.pnl_percent * 100 if position_summary.pnl_percent is not None else None
            col2.write(f"**Total PnL %:** {pnl_percent:.2f} %" if pnl_percent is not None else "N/A")

            st.space()
            with st.container(horizontal=True, horizontal_alignment="right"):
                if st.button("Edit position"):
                    st.session_state.position_id = selected_position_id
                    st.session_state.instrument_id = selected_instrument_id
                    st.switch_page("pages/positions_edit.py")

            # --- Trades -------------------------------------------------------------------------------------------

            st.divider()
            st.subheader("Trades:")
            position_trades = _trades_service.get_by_position(session, selected_position_id)
            if position_trades:
                trades_df = pd.DataFrame([{
                    "trade_id": t.id,
                    "Date": to_local(t.date),
                    "Type": "➕ BUY" if t.type.value == "buy" else "➖ SELL",
                    "Qty": t.quantity,
                    "Price": format_currency(t.price, currency_symbol),
                    "Total": format_currency(t.price * t.quantity, currency_symbol),
                } for t in position_trades])
                trades_dataframe = st.dataframe(
                    data=trades_df,
                    column_config={"trade_id": None},
                    hide_index=True,
                    on_select="rerun",
                    selection_mode="single-row",
                )
                if trades_dataframe["selection"]["rows"]:
                    trade_idx = trades_dataframe["selection"]["rows"][0]
                    selected_trade = position_trades[trade_idx]
                    with st.container(horizontal=True):
                        if st.button("Edit trade", key="trade_edit_btn"):
                            st.session_state.trade_id = selected_trade.id
                            st.switch_page("pages/trades_edit.py")
                        if st.button("Delete trade", type="primary", key="trade_delete_btn"):
                            confirm_delete_dialog(f"Are you sure you want to delete trade {selected_trade.id}?", selected_trade.id, delete_trade)
            else:
                st.info("No trades available")

            with st.container(horizontal=True, horizontal_alignment="right"):
                if st.button("Add new trade", key=f"add_trade_button_{selected_position_id}"):
                    st.session_state.trade_id = None
                    st.session_state.position_id = selected_position_id
                    st.switch_page("pages/trades_edit.py")

            # --- Transactions -------------------------------------------------------------------------------------

            st.divider()
            st.subheader("Transactions:")
            position_transactions = _transactions_service.get_by_position(session, selected_position_id)
            if position_transactions:
                txn_df = pd.DataFrame([{
                    "txn_id": t.id,
                    "Type": t.type.value,
                    "Amount": f"{t.amount:.2f} {currency_symbol}",
                    "Date": to_local(t.date),
                } for t in position_transactions])
                transactions_dataframe = st.dataframe(
                    data=txn_df,
                    column_config={"txn_id": None},
                    hide_index=True,
                    on_select="rerun",
                    selection_mode="single-row",
                )
                if transactions_dataframe["selection"]["rows"]:
                    txn_idx = transactions_dataframe["selection"]["rows"][0]
                    selected_transaction = position_transactions[txn_idx]
                    with st.container(horizontal=True):
                        if st.button("Edit transaction", type="secondary", key="txn_edit_btn"):
                            st.session_state.transaction_id = selected_transaction.id
                            st.switch_page("pages/transactions_edit.py")
                        if st.button("Delete transaction", type="primary", key="txn_delete_btn"):
                            confirm_delete_dialog(f"Are you sure you want to delete transaction {selected_transaction.id}?", selected_transaction.id, delete_transaction)
            else:
                st.info("No transactions available")

            with st.container(horizontal=True, horizontal_alignment="right"):
                if st.button("Add new transaction", key=f"add_trans_btn_{selected_position_id}"):
                    st.session_state.position_id = selected_position_id
                    st.switch_page("pages/transactions_edit.py")

        # --- Price chart ------------------------------------------------------------------------------------------

        st.space()
        with st.container(border=True):
            with get_session() as price_session:
                prices_list = _ohlcvs_service.get_prices_for_instrument(price_session, position_basic.instrument_id)

            if prices_list:
                prices_df = pd.DataFrame([p.model_dump(mode="json") for p in prices_list])
                fig = go.Figure(data=go.Ohlc(
                    x=prices_df['date'],
                    open=prices_df['open'],
                    high=prices_df['high'],
                    low=prices_df['low'],
                    close=prices_df['close'],
                ))

                if position_trades:
                    buy_trades = [t for t in position_trades if t.type.value == "buy"]
                    sell_trades = [t for t in position_trades if t.type.value == "sell"]
                    if buy_trades:
                        fig.add_trace(go.Scatter(
                            x=[t.date for t in buy_trades],
                            y=[t.price for t in buy_trades],
                            mode='markers',
                            name='BUY',
                            marker=dict(symbol='triangle-up', color='green', size=14, line=dict(width=1, color='darkgreen')),
                            hovertemplate='BUY<br>Price: %{y}<extra></extra>',
                        ))
                    if sell_trades:
                        fig.add_trace(go.Scatter(
                            x=[t.date for t in sell_trades],
                            y=[t.price for t in sell_trades],
                            mode='markers',
                            name='SELL',
                            marker=dict(symbol='triangle-down', color='red', size=14, line=dict(width=1, color='darkred')),
                            hovertemplate='SELL<br>Price: %{y}<extra></extra>',
                        ))

                fig.update_layout(
                    title=f"{position_basic.instrument_name} — Price History",
                    xaxis_title="Date",
                    yaxis_title="Price",
                    height=800,
                    hovermode="x unified",
                    xaxis=dict(showspikes=True, spikemode="across", spikesnap="cursor", spikecolor="gray", spikethickness=1),
                )
                st.plotly_chart(fig, key="position_ohlc_chart")
            else:
                st.info("No price data available for this instrument.")
