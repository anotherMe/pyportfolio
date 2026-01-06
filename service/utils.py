
import streamlit as st

from lib.settings_manager import get_timezone


DEFAULT_DATETIME_FORMAT = "%Y-%m-%d %H:%M"


def account_selector(accounts):

    if 'account' not in st.session_state:
        st.session_state.account = 'All'

    accounts_list = [account.name for account in accounts]
    accounts_list.append("All")

    # Retrieve current account from session
    current_account_name = st.session_state.account

    # Render selector in the sidebar
    selected = st.sidebar.selectbox(
        "Current Account",
        options=accounts_list,
        index=accounts_list.index(current_account_name),
        key="current_account",
        # help="Select the active account"
    )

    # Update session query param if it changed
    if selected != current_account_name:
        st.session_state.account = selected

def to_local(dt):
    if dt is None:
        return None
    return dt.astimezone(get_timezone()).strftime(DEFAULT_DATETIME_FORMAT)

def format_currency(amount, currency_symbol="€"):
    if amount is None:
        return "N/A"
    return f"{amount:.2f} {currency_symbol}"

def format_currency_color(amount, currency_symbol="€"):

    if amount < 0:
        color = "red"
    elif amount == 0:
        color = "gray"
    else:
        color = "green"

    if amount is None:
        return "N/A"
    return f":{color}-badge[{amount:.2f} {currency_symbol}]"