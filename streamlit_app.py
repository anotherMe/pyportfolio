import streamlit as st

st.set_page_config(page_title="My Portfolio Dashboard", layout="wide", initial_sidebar_state="expanded")

pages = [    
        st.Page("pages/overview.py", title="Overview", icon="📈"),
        st.Page("pages/instruments.py", title="🔧 Instruments"),
        st.Page("pages/trades.py", title="💼 Trades"),
        st.Page("pages/transactions.py", title="💰 Transactions"),
        st.Page("pages/settings.py", title="⚙️ Settings"),
    ]

nav = st.navigation(pages)
nav.run()
