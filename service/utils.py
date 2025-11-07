import streamlit as st


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

    # st.sidebar.caption(f"🔹 Active account: **{selected}**")
