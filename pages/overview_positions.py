
import streamlit as st

from lib.repo.accounts_repository import get_account_by_name, get_all_accounts
from lib.database import get_session
from lib.repo.portfolio_repository import get_positions_summary
from lib.streamlit.utils import account_selector

# --------------------------------------------------------------------------------
# -- utility functions

def style_positions(df):
    """Add formatted display columns and apply color styling with type icons."""

    # Create human-friendly display columns
    df["pnl_alt"] = df["pnl"]
    df["type_alt"] = df["type"]

    # Define coloring for PnL
    def style_pnl(v):
        color = "green" if v > 0 else "red" if v < 0 else "gray"
        return f"color: {color}; font-weight: bold;"

    # Format PnL numbers
    def format_pnl(v):
        return f"€{v:,.2f}"

    # Define icons for type
    def format_type(v):
        # 🔓 open | 🔒 closed
        # Alternatives: 🟢 / 🔴, ✅ / ❌, 🟩 / 🟥
        return "🔒" if v == "closed" else ""

    # Apply styles
    styled = (
        df.style
        .format({
            "pnl_alt": format_pnl,
            "type_alt": format_type,
        })
        .applymap(style_pnl, subset=["pnl_alt"])
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
    
    positions = get_positions_summary(session, current_account, include_closed=include_closed, include_open=include_open)

    # --- Show positions
    styled_positions = style_positions(positions)
    st.dataframe(
        data=styled_positions,
        column_config={
            "instrument": "Instrument",
            "instrument_id": None,
            "type": None,
            "type_alt": st.column_config.TextColumn(label="",width=1, help="Show if the position has been closed"),
            "date": st.column_config.DateColumn("Date"), # st.column_config.DatetimeColumn("Date")
            "quantity": None, # st.column_config.NumberColumn("Quantity"),
            "avg_price": st.column_config.NumberColumn("Avg buy price", format="euro"),
            "market_price": st.column_config.NumberColumn("Market price", format="euro"),
            "pnl": None, # st.column_config.NumberColumn("PNL", format="euro")
            "pnl_alt": "PNL",
            "pnl_type": None,
        },
        hide_index=True,
    )


    st.subheader("Totals")

    total_pnl = positions["pnl"].sum()
    color = "green" if total_pnl > 0 else "red"
    col1, col2 = st.columns([6,1])
    with col2:
        st.markdown(
            f"<h3>Total PnL: <span style='color:{color}'>{total_pnl:,.2f} €</span></h3>",
            unsafe_allow_html=True
        )