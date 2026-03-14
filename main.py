
import streamlit as st


st.set_page_config(page_title="My Portfolio Dashboard", layout="wide", initial_sidebar_state="collapsed")

pages = {
    "📊 Positions": [
        st.Page("pages/positions_list.py", title="List", default=True),
        st.Page("pages/positions_detail.py", title="Details"),
        st.Page("pages/positions_edit.py", title="Add / Edit"),
    ],
    "🏦 Accounts": [
        st.Page("pages/accounts_list.py", title="List"),
        st.Page("pages/accounts_edit.py", title="Add / Edit"),
    ],
    "🔧 Instruments": [    
        st.Page("pages/instruments_list.py", title="List"),
        st.Page("pages/instruments_detail.py", title="Details"),
        st.Page("pages/instruments_edit.py", title="Add / Edit"),
    ],
    "📈 Prices": [
        st.Page("pages/prices_load_yahoo.py", title="List"),
    ],
    "💼 Trades": [
        st.Page("pages/trades_list.py", title="List"),
        st.Page("pages/trades_detail.py", title="Details"),
        st.Page("pages/trades_edit.py", title="Add / Edit"),
    ],
    "💰 Transactions": [
        st.Page("pages/transactions_list.py", title="List"),
        st.Page("pages/transactions_detail.py", title="Details"),
        st.Page("pages/transactions_edit.py", title="Add / Edit"),
    ],
    "⚙️ Other": [
        st.Page("pages/backup.py", title="Backup", icon="💾"),
        st.Page("pages/demo_seed.py", title="Seed database", icon="🌱"),
        st.Page("pages/test.py", title="🧪 Test"),
    ]}

nav = st.navigation(pages)
nav.run()
