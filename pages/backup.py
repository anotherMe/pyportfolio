import shutil
from pathlib import Path
from datetime import datetime
import streamlit as st

st.set_page_config(page_title="DB Backup", page_icon="💾")

st.title("Create a backup of portfolio.db")
st.write("Click the button to create a timestamped copy of the database file.")

db_path_input = st.text_input("Database file path", value="portfolio.db")
db_path = Path(db_path_input)

if st.button("Create Backup"):
    if not db_path.exists():
        st.error(f"Source file not found: {db_path}")
    else:
        try:
            ts = datetime.now().strftime("%Y.%m.%d.%H.%M")
            backup_path = db_path.with_name(f"{db_path.name}.{ts}.bak")
            shutil.copy2(db_path, backup_path)
            st.success(f"Backup created: {backup_path}")
            with open(backup_path, "rb") as f:
                st.download_button("Download backup", data=f.read(), file_name=backup_path.name)
        except Exception as e:
            st.exception(e)