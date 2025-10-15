import streamlit as st
from lib.database import get_session
from lib.models import Instrument

st.title("✏️ Edit Instrument")

session = get_session()


