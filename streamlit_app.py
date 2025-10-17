import streamlit as st

st.set_page_config(page_title="My Portfolio Dashboard", layout="wide", initial_sidebar_state="expanded")

pages = {
    "🔧 Instruments": [    
        st.Page("pages/instruments_list.py", title="List"),
        st.Page("pages/instruments_details.py", title="Details"),
        st.Page("pages/instruments_edit.py", title="Add / Edit"),
    ],
    "Other": [
        st.Page("pages/trades.py", title="💼 Trades"),
        st.Page("pages/transactions.py", title="💰 Transactions"),
        st.Page("pages/overview.py", title="Overview", icon="📈"),
        st.Page("pages/settings.py", title="⚙️ Settings"),
        st.Page("pages/test.py", title="🧪 Test"),
    ]}

nav = st.navigation(pages)
nav.run()
