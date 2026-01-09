
import streamlit as st
from lib.database import get_session
from lib.models import Account

print("Running accounts edit page...")

if 'account_id' not in st.session_state:
    st.session_state.account_id = None

st.title("🔧 Accounts")

with get_session() as session, session.begin():
    
    if st.session_state.account_id:

        account = session.get(Account, st.session_state.account_id)

        with st.container(horizontal=True):
            st.subheader(f"Editing Account with ID: {st.session_state.account_id}")
            if st.button("Clear selection"):
                st.session_state.account_id = None
                st.rerun()
    
        # --- Account form ---
        with st.form("account_form"):
            account.name = st.text_input("Name", value=account.name or "")
            account.description = st.text_input("Description", value=account.description or "") 
            save = st.form_submit_button("💾 Save")

            if save:
                if not account.name:
                    st.warning("Name cannot be empty.")
                else:
                    session.add(account)
                    st.success("✅ Account saved successfully!")

    else:

        st.subheader("Add New Account")
        
        with st.form("account_form"):

            account = Account()
            account.name = st.text_input("Name")
            account.description = st.text_input("Description")

            col1, col2 = st.columns([7,1])
            with col2:
                save = st.form_submit_button("💾 Save")

            if save:
                if not account.name:
                    st.warning("Name cannot be empty.")
                else:
                    session.add(account)
                    st.session_state.account_id = None
                    st.success("✅ Account saved successfully!")
    
    col1, col2 = st.columns([5,1])
    with col2:
        if st.button("Back to list"):
            st.switch_page("pages/accounts_list.py")
