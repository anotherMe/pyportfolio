import streamlit as st
from datetime import date
from lib.db import get_session, to_cents, from_cents
from lib.models import Transaction, Instrument

st.title("💰 Dividends & Taxes")

tab1, tab2 = st.tabs(["📈 Dividends", "💸 Taxes"])

session = get_session()

# --- Fetch instruments for autocomplete ---
instruments = session.query(Instrument).order_by(Instrument.isin).all()
isin_map = {f"{inst.isin} — {inst.name or inst.ticker or ''}".strip(): inst.id for inst in instruments}
isin_options = list(isin_map.keys())

# --- DIVIDENDS TAB ---
with tab1:
    st.subheader("Add Dividend")

    with st.form("add_dividend_form"):
        isin_label = st.selectbox(
            "Instrument (ISIN)",
            options=["(none)"] + isin_options,
            index=0,
            help="Select the instrument that paid the dividend"
        )
        instrument_id = isin_map.get(isin_label) if isin_label != "(none)" else None
        dividend_date = st.date_input("Payment date", value=date.today())
        divident_time = st.time_input("Payment time", value="now", step=60)
        amount = st.number_input("Amount (€)", min_value=0.0, step=0.01)
        submitted = st.form_submit_button("Add Dividend")

        if submitted:
            div = Transaction(
                instrument_id=instrument_id,
                date=dividend_date,
                amount=to_cents(amount)
            )
            session.add(div)
            session.commit()
            st.success(f"Dividend for {instrument_id} added successfully!")

    st.divider()
    st.subheader("Dividend History")

    dividends = session.query(Transaction).where(Transaction.type == 'div').order_by(Transaction.date.desc()).all()
    if dividends:
        st.table([
            {
                "Instrument": d.trade.instrument_id,
                "Date": d.date.strftime("%Y-%m-%d"),
                "Amount (€)": from_cents(d.amount)
            } for d in dividends
        ])
    else:
        st.info("No dividends recorded yet.")


# --- TAXES TAB ---
with tab2:
    st.subheader("Add Tax")

    with st.form("add_tax_form"):
        description = st.text_input("Description")
        tax_date = st.date_input("Date", value=date.today())
        amount = st.number_input("Amount (€)", step=0.01, format="%.2f")
        submitted = st.form_submit_button("Add Tax")

        # if submitted:
        #     tax = Tax(
        #         description=description,
        #         date=tax_date,
        #         amount=int(amount * 100)
        #     )
        #     session.add(tax)
        #     session.commit()
        #     st.success("Tax added successfully!")

    st.divider()
    st.subheader("Tax History")

    taxes = session.query(Transaction).where(Transaction.type == 'tax').order_by(Transaction.date.desc()).all()
    if taxes:
        st.table([
            {
                "Description": t.description,
                "Date": t.date.strftime("%Y-%m-%d"),
                "Amount (€)": t.amount / 100
            } for t in taxes
        ])
    else:
        st.info("No taxes recorded yet.")
