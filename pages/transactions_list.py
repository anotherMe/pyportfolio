
import streamlit as st
from lib.accounts_repository import get_account_by_name, get_all_accounts
from lib.database import get_session, read_from_db
from lib.models import Transaction, Instrument
from lib.streamlit.utils import account_selector
from lib.transactions_repository import get_all_transactions

print("Running transactions page...")

st.title("💰 Transactions")

with get_session() as session:

    # --- Account selector ---
    accounts = get_all_accounts(session)
    account_selector(accounts) # Show sidebar account selector
    current_account = get_account_by_name(session, st.session_state.account)

    tab1, tab2, tab3, tab4 = st.tabs(["All", "📈 Dividends", "💸 Taxes", "Fees"])

    instruments = session.query(Instrument).order_by(Instrument.isin).all()
    if not instruments:
        st.info("No instruments found. Please add instruments first.")
        st.stop()

    isin_map = {f"{inst.isin} — {inst.name or inst.ticker or ''}".strip(): inst.id for inst in instruments}
    isin_options = list(isin_map.keys())

    # --- ALL TRANSACTIONS TAB ---
    with tab1:
        
        st.subheader("All Transactions")

        transactions = get_all_transactions(session, current_account)
        if transactions:
            st.dataframe(data=[
                {
                    "Type": t.type,
                    "Instrument": t.trade.instrument.name if t.trade else "",
                    "Date": t.date.strftime("%Y-%m-%d"),
                    "Amount (€)": read_from_db(t.amount),
                    "Description": t.description or ""
                } for t in transactions
            ])
        else:
            st.info("No transactions recorded yet.")

    # --- DIVIDENDS TAB ---
    with tab2:

        st.subheader("Dividend History")

        dividends = session.query(Transaction).where(Transaction.type == 'div').order_by(Transaction.date.desc()).all()
        if dividends:
            st.dataframe(data=[
                {
                    "Instrument": d.trade.instrument.name,
                    "Date": d.date.strftime("%Y-%m-%d"),
                    "Amount (€)": read_from_db(d.amount)
                } for d in dividends
            ])
        else:
            st.info("No dividends recorded yet.")


    # --- TAXES TAB ---
    with tab3:

        st.subheader("Tax History")

        taxes = session.query(Transaction).where(Transaction.type == 'tax').order_by(Transaction.date.desc()).all()
        if taxes:
            st.dataframe(data=[
                {
                    "Description": t.description,
                    "Date": t.date.strftime("%Y-%m-%d"),
                    "Amount (€)": read_from_db(t.amount)
                } for t in taxes
            ])
        else:
            st.info("No taxes recorded yet.")

    # --- FEES TAB ---
    with tab4:

        st.subheader("Fee History")

        fees = session.query(Transaction).where(Transaction.type == 'fee').order_by(Transaction.date.desc()).all()
        if fees:
            st.dataframe(data=[
                {
                    "Description": f.description,
                    "Date": f.date.strftime("%Y-%m-%d"),
                    "Amount (€)": read_from_db(f.amount)
                } for f in fees
            ])
        else:
            st.info("No fees recorded yet.")