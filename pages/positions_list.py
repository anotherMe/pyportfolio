
import pandas as pd
import streamlit as st

from lib.repo.accounts_repository import get_account_by_name, get_all_accounts
from lib.database import get_session
from service.positions_service import get_positions_summary
from service.utils import account_selector


# --------------------------------------------------------------------------------
# -- utility functions

def format_and_style_positions(df):
    """Add formatted display columns and apply color styling with type icons."""

    # Create human-friendly display columns
    pnl_styled_col = df["pnl"]
    transactions_amount_col = df["transactions_amount"]
    pnl_percent_styled_col = df["pnl_percent"]
    opening_date_styled_col = df["opening_date"]
    closing_date_styled_col = df["closing_date"]

    df.insert(len(df.columns), "pnl_styled", pnl_styled_col)
    df.insert(len(df.columns), "transactions_amount_styled", transactions_amount_col)
    df.insert(len(df.columns), "pnl_percent_styled", pnl_percent_styled_col)
    df.insert(5, "opening_date_styled", opening_date_styled_col)
    df.insert(len(df.columns), "closing_date_styled", closing_date_styled_col)

    def color_price(v):
        color = "green" if v > 0 else "red" if v < 0 else "gray"
        return f"color: {color}; font-weight: bold;"

    def format_price(v):
        return f"{v:,.2f} €"  # TODO: manage currency dynamically ?

    def format_percent(v):
        return f"{v*100:,.2f} %"

    def format_date(v):
        return "" if pd.isna(v) else v.strftime('%Y-%m-%d %H:%M:%S')

    # Apply styles
    styled = (
        df.style
        .format({
            "pnl_styled": format_price,
            "pnl_percent_styled": format_percent,
            "transactions_amount_styled": format_price,
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

st.title("📈 Current market positions")

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


with get_session() as session:

    # --- Account selector ---
    accounts = get_all_accounts(session)
    account_selector(accounts) # Show sidebar account selector
    current_account = get_account_by_name(session, st.session_state.account)

    # --- Retrieve Open/Closed positions ---

    include_closed = True
    include_open = True
    if st.session_state.status_filter == 'open':
        include_closed=False
    elif st.session_state.status_filter == 'closed':
        include_open=False
    
    positions_df = get_positions_summary(session, include_closed, include_open, current_account)

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
            "account_id": None,
            "position_id": None,
            "opening_date": None,
            "opening_date_styled": "First buy on",
            "instrument_id": None,
            "instrument_name": "Instrument",
            "instrument_isin": None,
            "instrument_ticker": None,
            "remaining_quantity": None,
            "remaining_cost_basis": None,
            "position_closed": "Remaining Qty",
            "avg_buy_price": None,
            # "total_invested": st.column_config.NumberColumn("Total buy cost", format="euro"),
            "total_invested": None,
            "closing_price": st.column_config.NumberColumn("Market price", format="euro"),
            "realized_pnl": None,
            "realized_pnl_percent": None,
            "latest_price": None,
            "latest_price_date": None,
            "unrealized_pnl": None,
            "unrealized_pnl_percent": None,
            "pnl": None,
            "pnl_styled": st.column_config.NumberColumn("PnL", format="euro"),
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

    # --- If a row has been selected, show buttons

    if st_dataframe["selection"]["rows"]:
        dataframe_index = st_dataframe["selection"]["rows"][0]
        # selected_position_id = filtered_positions_df.iloc[dataframe_index].position_id.item()
        selected_instrument_id = filtered_positions_df.iloc[dataframe_index].instrument_id.item()
        with st.container(horizontal=True):
            # st.space("stretch")
            if st.button("Instrument details"):
                st.session_state.instrument_id = selected_instrument_id
                st.switch_page("pages/instruments_detail.py")
            # if st.button("Edit position"):
            #     st.session_state.position_id = selected_position_id
            #     st.session_state.instrument_id = selected_instrument_id
            #     st.switch_page("pages/positions_edit.py")
            # if st.button("Position details"):
            #     st.session_state.position_id = selected_position_id
            #     st.switch_page("pages/positions_detail.py")


    # --- Totals --- 

    total_invested_sum = filtered_positions_df["total_invested"].sum()
    total_pnl = (filtered_positions_df["realized_pnl"] + filtered_positions_df["unrealized_pnl"]).sum()
    total_percent_pnl = 0

    color = "green" if total_pnl > 0 else "red"
    col1, col2 = st.columns([2,1])
    with col2:
        st.markdown(
            f"<h3>Total buy: <span>{total_invested_sum:,.2f} €</span></h3>",
            unsafe_allow_html=True
        )
        st.markdown(
            f"<h3>Total PnL: <span style='color:{color}'>{total_pnl:,.2f} €</span></h3>",
            unsafe_allow_html=True
        )
