
import streamlit as st


st.set_page_config(page_title="My Portfolio Dashboard", layout="wide", initial_sidebar_state="collapsed")

pages = {
    "📈 Overview": [
        st.Page("pages/overview_fifo_pnl.py", title="FIFO PnL"),
        st.Page("pages/overview_open_positions.py", title="Open positions"),
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
        # st.Page("pages/settings.py", title="⚙️ Settings"),
        st.Page("pages/backup.py", title="Backup", icon="💾"),
        # st.Page("pages/test.py", title="🧪 Test"),
    ]}

nav = st.navigation(pages)
nav.run()
