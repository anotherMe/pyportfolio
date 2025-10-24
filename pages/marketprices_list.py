import streamlit as st
import pandas as pd

from lib.database import get_session
from lib.repo.prices_repository import get_latest_closing_prices

st.title("📊 Latest Closing Prices")

# Open a session
with get_session() as session:
    results = get_latest_closing_prices(session)


# Convert to DataFrame
df = pd.DataFrame(results, columns=["Instrument", "Last Close", "Timestamp"])

# Handle missing values
df["Last Close"] = df["Last Close"].fillna("—")
df["Timestamp"] = df["Timestamp"].fillna("—")

# Show dataframe in Streamlit
st.dataframe(
    df,
    use_container_width=True,
    hide_index=True
)
