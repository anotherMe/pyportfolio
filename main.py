
import streamlit as st

from lib.database import get_session
from lib.repo.accounts_repository import get_all_accounts
from service.utils import account_selector


st.set_page_config(page_title="My Portfolio Dashboard", layout="wide", initial_sidebar_state="collapsed")

all_pages = [

    st.Page("pages/dashboard.py",           title="Dashboard", default=True),
    st.Page("pages/positions_list.py",      title="Positions"),
    st.Page("pages/positions_detail.py",    title="Position Detail"),
    st.Page("pages/positions_edit.py",      title="Position Edit"),
    st.Page("pages/accounts_list.py",       title="Accounts"),
    st.Page("pages/accounts_edit.py",       title="Account Edit"),
    st.Page("pages/instruments_list.py",    title="Instruments"),
    st.Page("pages/instruments_detail.py",  title="Instrument Detail"),
    st.Page("pages/instruments_edit.py",    title="Instrument Edit"),
    st.Page("pages/prices_list.py",         title="Prices"),
    st.Page("pages/trades_list.py",         title="Trades"),
    st.Page("pages/trades_detail.py",       title="Trade Detail"),
    st.Page("pages/trades_edit.py",         title="Trade Edit"),
    st.Page("pages/transactions_list.py",   title="Transactions"),
    st.Page("pages/transactions_detail.py", title="Transaction Detail"),
    st.Page("pages/transactions_edit.py",   title="Transaction Edit"),
    st.Page("pages/backup.py",              title="Backup"),
    st.Page("pages/demo_seed.py",           title="Seed database"),
    st.Page("pages/test.py",                title="Test"),
]

nav = st.navigation(all_pages, position="hidden")

with st.sidebar:
    st.page_link("pages/dashboard.py",         label="Dashboard")
    st.page_link("pages/positions_list.py",    label="Positions")
    st.page_link("pages/instruments_list.py",  label="Instruments")
    st.page_link("pages/trades_list.py",       label="Trades")
    st.page_link("pages/transactions_list.py", label="Transactions")
    st.page_link("pages/accounts_list.py",     label="Accounts")
    st.page_link("pages/prices_list.py",       label="Prices")
    st.divider()
    st.page_link("pages/backup.py",            label="Backup")
    st.page_link("pages/demo_seed.py",         label="Seed database")
    st.page_link("pages/test.py",              label="Test")
    st.divider()
    with get_session() as session:
        accounts = get_all_accounts(session)
        account_selector(accounts)
    st.divider()

nav.run()
