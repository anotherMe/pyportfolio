import streamlit as st

st.set_page_config(page_title="My Portfolio Dashboard", layout="wide", initial_sidebar_state="expanded")

pages = [    
        st.Page("pages/overview.py", title="Portfolio Overview"),
        st.Page("pages/instruments.py", title="Instruments"),
        st.Page("pages/trades.py", title="Trades"),
        st.Page("pages/transactions.py", title="Dividends & Taxes"),
        st.Page("pages/settings.py", title="Settings"),
    ]

nav = st.navigation(pages)
nav.run()
