import streamlit as st

from lib.accounts_repository import get_account_by_name


def account_selector(account_list):
    """Show and persist the currently selected account via query params."""

    # Determine current account from URL or fallback
    current_account = st.query_params.get("account", [account_list[0]])[0]

    # Render selector in the sidebar
    selected = st.sidebar.selectbox(
        "Current Account",
        options=account_list,
        index=account_list.index(current_account) if current_account in account_list else 0,
        key="current_account",
        # help="Select the active account"
    )

    # Update URL query param if it changed
    if selected != current_account:
        st.query_params["account"] = selected

    # st.sidebar.caption(f"🔹 Active account: **{selected}**")

def extract_current_account_from_params(session):
    if not st.query_params.get("account"):
        st.query_params.account = "All"
    if st.query_params.account:
        return get_account_by_name(session, st.query_params.account)
    else:
        return None