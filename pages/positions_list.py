
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
    pnl_percent_styled_col = df["pnl_percent"]
    opening_date_styled_col = df["opening_date"]
    closing_date_styled_col = df["closing_date"]

    df.insert(len(df.columns), "pnl_styled", pnl_styled_col)
    df.insert(len(df.columns), "pnl_percent_styled", pnl_percent_styled_col)
    df.insert(5, "opening_date_styled", opening_date_styled_col)
    df.insert(len(df.columns), "closing_date_styled", closing_date_styled_col)

    def style_pnl(v):
        color = "green" if v > 0 else "red" if v < 0 else "gray"
        return f"color: {color}; font-weight: bold;"

    def format_pnl(v):
        return f"{v:,.2f} €"  # TODO: add currency ?

    def format_pnl_percent(v):
        return f"{v*100:,.2f} %"

    def format_date(v):
        return "" if pd.isna(v) else v.strftime('%Y-%m-%d %H:%M:%S')

    # Apply styles
    styled = (
        df.style
        .format({
            "pnl_styled": format_pnl,
            "pnl_percent_styled": format_pnl_percent,
            "closing_date_styled": format_date,
            "opening_date_styled": format_date,
        })
        .map(style_pnl, subset=["pnl_styled", "pnl_percent_styled"])
    )

    return styled


# --------------------------------------------------------------------------------
# -- Streamlit page

# Initialize the session state variable if it doesn't exist
if "status_filter" not in st.session_state:
    st.session_state.status_filter = "all"

st.title("📈 Current market positions")

options = {
    "Show all positions": "all",
    "Show open positions": "open",
    "Show closed positions": "closed"
}
# Create the selectbox and bind it to the session state
# Show the selectbox with display labels
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

    # --- Retrieve positions ---
    include_closed = True
    include_open = True
    if st.session_state.status_filter == 'open':
        include_closed=False
    elif st.session_state.status_filter == 'closed':
        include_open=False
    
    positions_df = get_positions_summary(session, current_account, include_closed=include_closed, include_open=include_open)

    # --- Show dataframe

    styled_positions = format_and_style_positions(positions_df)
    st_dataframe = st.dataframe(
        data=styled_positions,
        column_config={
            "position_id": None,
            "opening_date": None,
            "opening_date_styled": "Opened on",
            "instrument_id": None,
            "instrument_name": "Instrument",
            "remaining_quantity": st.column_config.NumberColumn("Qty left"),
            # "avg_buy_price": st.column_config.NumberColumn("Avg buy price", format="euro"),
            "avg_buy_price": None,
            # "total_buy_cost": st.column_config.NumberColumn("Total buy cost", format="euro"),
            "total_buy_cost": None,
            "closing_price": st.column_config.NumberColumn("Market price", format="euro"),
            "realized_pnl": None,
            "latest_price": None,
            "latest_price_date": None,
            "unrealized_pnl": None,
            "pnl": None,
            "pnl_styled": st.column_config.NumberColumn("PnL", format="euro"),
            # FIXME: show this later
            # "transactions_amount": st.column_config.NumberColumn("Transactions amount", format="euro"),
            "transactions_amount": None,
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
        selected_position_id = positions_df.iloc[dataframe_index].position_id.item()
        selected_instrument_id = positions_df.iloc[dataframe_index].instrument_id.item()
        with st.container(horizontal=True):
            # st.space("stretch")
            if st.button("Instrument details"):
                st.session_state.instrument_id = selected_instrument_id
                st.switch_page("pages/instruments_detail.py")
            if st.button("Position details"):
                st.session_state.position_id = selected_position_id
                st.switch_page("pages/positions_detail.py")


    # --- Totals --- 

    total_buy_price = positions_df["avg_buy_price"].dot(positions_df["remaining_quantity"])  # FIXME: is this correct?
    total_pnl = (positions_df["realized_pnl"] + positions_df["unrealized_pnl"]).sum()
    total_percent_pnl = 0

    color = "green" if total_pnl > 0 else "red"
    col1, col2 = st.columns([2,1])
    with col2:
        st.markdown(
            f"<h3>Total buy: <span style='color:{color}'>{total_buy_price:,.2f} €</span></h3>",
            unsafe_allow_html=True
        )
        st.markdown(
            f"<h3>Total PnL: <span style='color:{color}'>{total_pnl:,.2f} €</span></h3>",
            unsafe_allow_html=True
        )
