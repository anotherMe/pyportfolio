
import streamlit as st


tab = st.radio("Select view:", ["Overview", "Details"], key="tabs")

if tab == "Overview":
    st.write("Showing overview content.")
else:
    st.write("Showing details content.")
