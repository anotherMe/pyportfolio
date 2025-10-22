
import streamlit as st

from lib.repo.accounts_repository import get_account_by_name, get_all_accounts
from lib.database import get_session
from lib.repo.portfolio_repository import get_open_positions
from lib.streamlit.utils import account_selector

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

    positions = get_open_positions(session, current_account)
    if positions.empty:
        st.info("Nothing to see here")
    else:

        if st.session_state.status_filter == 'open':
            filtered_positions = positions[positions["quantity"] > 0]
        elif st.session_state.status_filter == 'closed':
            filtered_positions = positions[positions["quantity"] == 0]
        else:
            filtered_positions = positions

        # Add a visual indicator column
        filtered_positions["value_alt"] = filtered_positions["value"].apply(
            lambda x: (
                f"🟢 €{x:,.2f}" if x > 0
                else f"🔴 €{x:,.2f}" if x < 0
                else f"⚪ €{x:,.2f}"
            )
        )

        st.dataframe(
            data=filtered_positions,
            column_config={
                "instrument": "Instrument",
                "quantity": st.column_config.NumberColumn("Quantity"),
                "value": None, # hide colum
                "value_alt": st.column_config.NumberColumn("Value (€)", format="euro"),
            },
            hide_index=True,
        )

        # --- Compute totals ---
        total_value = filtered_positions["value"].sum()
        total_quantity = filtered_positions["quantity"].sum()
        avg_value = filtered_positions["value"].mean()

        # --- Totals block ---
        st.markdown("#### Totals")
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Quantity", f"{total_quantity:,.0f}")
        c2.metric("Average Value", f"€{avg_value:,.2f}")
        c3.metric("Total Value", f"€{total_value:,.2f}")