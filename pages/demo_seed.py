# streamlit_app/pages/Seed Demo Data.py

import streamlit as st
from lib.database import get_session, init_db
from lib.demo_seed import seed_demo_data

st.set_page_config(page_title="Seed Demo Data", page_icon="🌱")

st.title("🌱 Seed Demo Database")

st.markdown("""
Use this page to populate the database with **fake demo data**.
Useful for presentations or testing without exposing real data.
""")

session = get_session()

# Optional: toggle to reset existing data
reset_db = st.checkbox("Reset existing data before seeding (dangerous!)")

if st.button("🚀 Seed Demo Data", type="primary"):
    try:
        init_db()  # make sure tables exist
        num_accounts, num_instruments, num_trades = seed_demo_data(session, reset=reset_db)
        st.success(f"✅ Demo data created successfully!")
        st.info(f"Accounts: {num_accounts}, Instruments: {num_instruments}, Trades: {num_trades}")
    except Exception as e:
        st.error(f"❌ Error while seeding: {e}")
else:
    st.caption("Click the button above to generate demo data.")
