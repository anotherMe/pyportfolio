
import streamlit as st

from lib.repo.accounts_repository import get_account_by_name, get_all_accounts
from lib.database import get_session
from lib.repo.portfolio_repository import get_open_positions
from lib.streamlit.utils import account_selector


st.title("📈 Open Positions")

with get_session() as session:

    # --- Account selector ---
    accounts = get_all_accounts(session)
    account_selector(accounts) # Show sidebar account selector
    current_account = get_account_by_name(session, st.session_state.account)
        
    positions = get_open_positions(session, current_account)

    if positions.empty:
        st.info("No open positions.")
    else:
        st.dataframe(
            positions,
            column_config={
                "instrument": "Instrument",
                "net_qty": st.column_config.NumberColumn("Quantity", format="%.2f"),
                "avg_buy_price": st.column_config.NumberColumn("Avg Buy Price (€)", format="%.2f"),
            },
            hide_index=True,
            use_container_width=True,
        )
