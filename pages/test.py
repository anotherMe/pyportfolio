import streamlit as st

st.title("Test page")

st.toast("Hello")
if st.button("Push me"):
    st.rerun()