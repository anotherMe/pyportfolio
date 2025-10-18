

from datetime import date
import streamlit as st
from lib.database import get_session, to_cents
from lib.models import Transaction
from lib.models import Instrument, Trade


print("Running transactions edit page...")

if 'transaction_id' not in st.session_state:
    st.session_state.transaction_id = None


st.title("💰 Transactions")

with get_session() as session, session.begin():

    if st.session_state.transaction_id:

        st.subheader("Edit Transaction")

        transaction = session.get(Transaction, st.session_state.transaction_id)
        if not transaction:
            st.error("Transaction not found.")
        else:
            
            # --- Transaction form ---
            with st.form("dividend_form"):

                st.selectbox(
                    "Transaction Type",
                    options=["div", "tax", "fee"],
                    index=["div", "tax", "fee"].index(transaction.type),
                    disabled=False
                )
                transaction_date = st.date_input("Transaction date", value=transaction.date)
                transaction_time = st.time_input("Transaction time", value=transaction.date.time(), step=60)
                amount = st.number_input("Amount (€)", min_value=0.0, step=0.01, value=transaction.amount / 100)
                submitted = st.form_submit_button("Save Transaction")

                if submitted:
                    transaction.date = date.combine(transaction_date, transaction_time)
                    transaction.amount = to_cents(amount)
                    session.add(transaction)
                    st.success(f"Transaction for {transaction.transaction_id} updated successfully!")

    else:

        st.subheader("Add transaction")
        transaction = Transaction()
        with st.form("add_transaction_form"):

            st.selectbox(
                "Transaction Type",
                options=["div", "tax", "fee"],
                disabled=False
            )
            
            # --- Instrument (optional) ---
            instruments = session.query(Instrument).all()
            def _inst_label(i):
                sym = getattr(i, "symbol", None)
                name = getattr(i, "name", None)
                if sym and name:
                    return f"{sym} — {name}"
                return sym or name or str(i)

            instrument_options = ["(none)"] + [_inst_label(i) for i in instruments]
            selected_instrument_label = st.selectbox("Instrument (optional)", options=instrument_options, index=0)
            selected_instrument = None
            if selected_instrument_label != "(none)":
                idx = instrument_options.index(selected_instrument_label) - 1
                selected_instrument = instruments[idx]
                # try to attach the relationship or fallback to id
                try:
                    transaction.instrument = selected_instrument
                except Exception:
                    transaction.instrument_id = getattr(selected_instrument, "id", None)

            # --- Trade (optional) ---
            trades = session.query(Trade).all()
            def _trade_label(t):
                d = getattr(t, "date", None)
                desc = getattr(t, "description", None) or getattr(t, "type", None) or ""
                if d:
                    return f"{d} — {desc}".strip(" — ")
                return desc or str(t)

            trade_options = ["(none)"] + [_trade_label(t) for t in trades]
            selected_trade_label = st.selectbox("Trade (optional)", options=trade_options, index=0)
            selected_trade = None
            if selected_trade_label != "(none)":
                idx = trade_options.index(selected_trade_label) - 1
                selected_trade = trades[idx]
                try:
                    transaction.trade = selected_trade
                except Exception:
                    transaction.trade_id = getattr(selected_trade, "id", None)

            transaction_date = st.date_input("Transaction date", value=date.today())
            transaction_time = st.time_input("Transaction time", value="now", step=60)
            transaction.amount = st.number_input("Amount (€)", min_value=0.0, step=0.01)

            col1, col2 = st.columns([7,1])
            with col2:
                save = st.form_submit_button("💾 Save")

            if save:
                transaction.date = date.combine(transaction_date, transaction_time)
                if not transaction.date:
                    st.warning("Date cannot be empty.")
                elif not transaction.type:
                    st.warning("Type cannot be empty.")
                elif transaction.amount <= 0:
                    st.warning("Amount must be greater than zero.")
                else:
                    session.add(transaction)
                    st.session_state.transaction_id = None
                    st.success("✅ Transaction saved successfully!")


    col1, col2 = st.columns([5,1])
    with col2:
        if st.button("Back to details"):
            st.switch_page("pages/transactions_details.py")