import streamlit as st
from lib.settings_manager import load_settings, save_settings
from lib.database import init_engine

st.title("⚙️ Settings")

settings = load_settings()

db_path = st.text_input("Database path", value=settings["database"]["url"])
default_timezone = st.text_input("Default timezone", value=settings["app"]["default_timezone"])

if st.button("💾 Save & Reload"):
    settings["database"]["url"] = db_path
    settings["app"]["default_timezone"] = default_timezone
    save_settings(settings)
    init_engine()  # <— reinitialize database connection
    st.success("Settings saved and database connection reloaded!")
