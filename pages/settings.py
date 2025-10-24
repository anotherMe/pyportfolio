import streamlit as st
from lib.settings_manager import load_settings, save_settings
from lib.database import init_engine

st.title("⚙️ Settings")

settings = load_settings()

db_path = st.text_input("Database path", value=settings["database"]["path"])
db_path = st.text_input("Database path", value=settings["app"]["decimal_precision"])

if st.button("💾 Save & Reload"):
    settings["database"]["path"] = db_path
    save_settings(settings)
    init_engine()  # <— reinitialize database connection
    st.success("Settings saved and database connection reloaded!")
