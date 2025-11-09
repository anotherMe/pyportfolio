
import streamlit as st
from lib.repo.accounts_repository import get_account_by_name, get_all_accounts
from lib.database import get_session, read_from_db
from lib.models import Transaction, Instrument
from lib.utils import confirm_delete_dialog
from service.utils import account_selector, to_local
import lib.repo.transactions_repository as transactions_repo

from logging_config import setup_logger
log = setup_logger(__name__)

log.debug("Running transactions page...")

def delete_transaction(item_id):
    with get_session() as session, session.begin():
        try:
            transactions_repo.delete_transaction(session, item_id)
            session.commit()
        except Exception:
            log.exception("")
            st.error(f"Error while deleting item {item_id}")

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

        transactions = transactions_repo.get_all_transactions(session, current_account)
        
        if transactions:
            st_dataframe = st.dataframe(data=[
                {
                    "Type": t.type,
                    "Instrument": t.trade.instrument.name if t.trade else "",
                    "Date": to_local(t.date),
                    "Amount (€)": read_from_db(t.amount),
                    "Description": t.description or ""
                } for t in transactions
            ],
            on_select="rerun", 
            selection_mode="single-row")
        else:
            st.info("No transactions recorded yet.")

    # # --- DIVIDENDS TAB ---
    # with tab2:

    #     st.subheader("Dividend History")

    #     dividends = session.query(Transaction).where(Transaction.type == 'div').order_by(Transaction.date.desc()).all()
    #     if dividends:
    #         st.dataframe(data=[
    #             {
    #                 "Instrument": d.trade.instrument.name,
    #                 "Date": to_local(d.date),
    #                 "Amount (€)": read_from_db(d.amount)
    #             } for d in dividends
    #         ],
    #         on_select="rerun", 
    #         selection_mode="single-row")
    #     else:
    #         st.info("No dividends recorded yet.")


    # # --- TAXES TAB ---
    # with tab3:

    #     st.subheader("Tax History")

    #     taxes = session.query(Transaction).where(Transaction.type == 'tax').order_by(Transaction.date.desc()).all()
    #     if taxes:
    #         st.dataframe(data=[
    #             {
    #                 "Description": t.description,
    #                 "Date": to_local(t.date),
    #                 "Amount (€)": read_from_db(t.amount)
    #             } for t in taxes
    #         ],
    #         on_select="rerun", 
    #         selection_mode="single-row")
    #     else:
    #         st.info("No taxes recorded yet.")

    # # --- FEES TAB ---
    # with tab4:

    #     st.subheader("Fee History")

    #     fees = session.query(Transaction).where(Transaction.type == 'fee').order_by(Transaction.date.desc()).all()
    #     if fees:
    #         st.dataframe(data=[
    #             {
    #                 "Description": f.description,
    #                 "Date": to_local(f.date),
    #                 "Amount (€)": read_from_db(f.amount)
    #             } for f in fees
    #         ],
    #         on_select="rerun", 
    #         selection_mode="single-row")
    #     else:
    #         st.info("No fees recorded yet.")

    if st_dataframe["selection"]["rows"]:
        dataframe_index = st_dataframe["selection"]["rows"][0]
        selected_transaction: Transaction = transactions[dataframe_index]
        with st.container(horizontal=True):
            st.space("stretch")
            if st.button("Show details"):
                st.session_state.transaction_id = selected_transaction.id
                st.switch_page("pages/transactions_edit.py")
            if st.button("Delete", type="primary"):
                confirm_delete_dialog(f"Are you sure you want to delete transaction {selected_transaction.id} ?", selected_transaction.id, delete_transaction)
