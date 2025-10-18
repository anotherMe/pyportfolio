
import streamlit as st
from lib.database import get_session, from_cents
from lib.models import Transaction, Instrument

print("Running transactions page...")

st.title("💰 Transactions")

with get_session() as session:

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

        transactions = session.query(Transaction).order_by(Transaction.date.desc()).all()
        if transactions:
            st.dataframe(data=[
                {
                    "Type": t.type,
                    "Instrument": t.trade.instrument_id if t.trade else "",
                    "Date": t.date.strftime("%Y-%m-%d"),
                    "Amount (€)": from_cents(t.amount),
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
                    "Instrument": d.trade.instrument_id,
                    "Date": d.date.strftime("%Y-%m-%d"),
                    "Amount (€)": from_cents(d.amount)
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
                    "Amount (€)": t.amount / 100
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
                    "Amount (€)": f.amount / 100
                } for f in fees
            ])
        else:
            st.info("No fees recorded yet.")