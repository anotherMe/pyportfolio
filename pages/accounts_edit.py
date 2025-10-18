import streamlit as st
from lib.database import get_session
from lib.models import Account

print("Running accounts edit page...")

st.title("🔧 Accounts")

if 'account_id' not in st.session_state:
    st.session_state.account_id = None

with get_session() as session, session.begin():
    
    if st.session_state.account_id:

        st.subheader("Edit Account")

        acc = session.get(Account, st.session_state.account_id)
        if not acc:
            st.error("Account not found.")
        else:
            
            # --- Account form ---
            with st.form("account_form"):
                acc.name = st.text_input("Name", value=acc.name or "")
                acc.description = st.text_input("Description", value=acc.description or "") 
                save = st.form_submit_button("💾 Save")

                if save:
                    if not acc.name:
                        st.warning("Name cannot be empty.")
                    else:
                        session.add(acc)
                        st.success("✅ Account saved successfully!")

    else:

        st.subheader("Add New Account")
        
        with st.form("account_form"):

            acc = Account()
            acc.name = st.text_input("Name")
            acc.description = st.text_input("Description")

            col1, col2 = st.columns([7,1])
            with col2:
                save = st.form_submit_button("💾 Save")

            if save:
                if not acc.name:
                    st.warning("Name cannot be empty.")
                else:
                    session.add(acc)
                    st.session_state.account_id = None
                    st.success("✅ Account saved successfully!")
    
    col1, col2 = st.columns([5,1])
    with col2:
        if st.button("Back to list"):
            st.switch_page("pages/accounts_list.py")
