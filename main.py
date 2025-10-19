
import streamlit as st
from lib.accounts_repository import get_all_accounts
from lib.database import get_session
from lib.streamlit.account_selector import account_selector
from pages import accounts_list


st.set_page_config(page_title="My Portfolio Dashboard", layout="wide", initial_sidebar_state="collapsed")

# Setup account selector
with get_session() as session, session.begin():
    accounts = get_all_accounts(session)
    accounts_list = [account.name for account in accounts]
    accounts_list.append("All")
account_selector(accounts_list)


pages = {
    "": [
        st.Page("pages/overview.py", title="Overview", icon="📈"),
    ],
    "🏦 Accounts": [
        st.Page("pages/accounts_list.py", title="List"),
        st.Page("pages/accounts_edit.py", title="Add / Edit"),
    ],
    "🔧 Instruments": [    
        st.Page("pages/instruments_list.py", title="List"),
        st.Page("pages/instruments_details.py", title="Details"),
        st.Page("pages/instruments_edit.py", title="Add / Edit"),
    ],
    "💼 Trades": [
        st.Page("pages/trades_list.py", title="List"),
        st.Page("pages/trades_details.py", title="Details"),
        st.Page("pages/trades_edit.py", title="Add / Edit"),
    ],
    "💰 Transactions": [
        st.Page("pages/transactions_list.py", title="List"),
        st.Page("pages/transactions_details.py", title="Details"),
        st.Page("pages/transactions_edit.py", title="Add / Edit"),
    ],
    "Other": [
        st.Page("pages/settings.py", title="⚙️ Settings"),
        st.Page("pages/backup.py", title="Backup", icon="💾"),
        # st.Page("pages/test.py", title="🧪 Test"),
    ]}

nav = st.navigation(pages)
nav.run()
