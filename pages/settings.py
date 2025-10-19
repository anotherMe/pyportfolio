import streamlit as st
import json
import os

SETTINGS_FILE = "settings.json"

st.title("⚙️ Settings")

# Load settings
if os.path.exists(SETTINGS_FILE):
    with open(SETTINGS_FILE, "r") as f:
        settings = json.load(f)
else:
    settings = {
        "default_currency": "EUR",
        "db_path": "portfolio.db",
        "decimal_precision": 6
    }

with st.form("settings_form"):
    st.subheader("Application Settings")

    settings["default_currency"] = st.text_input(
        "Default Currency", value=settings.get("default_currency", "EUR")
    )
    settings["db_path"] = st.text_input(
        "Database Path", value=settings.get("db_path", "portfolio.db")
    )
    settings["decimal_precision"] = st.number_input(
        "Decimal Precision", min_value=0, max_value=6, value=settings.get("decimal_precision", 6)
    )

    submitted = st.form_submit_button("💾 Save Settings")

    if submitted:
        with open(SETTINGS_FILE, "w") as f:
            json.dump(settings, f, indent=2)
        st.success("Settings saved successfully!")

st.divider()

st.write("**Current Settings:**")
st.json(settings)
