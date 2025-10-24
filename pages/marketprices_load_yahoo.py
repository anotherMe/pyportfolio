
import streamlit as st

from lib.myYahooFinance import YahooSymbolParser
from lib.repo.portfolio_repository import load_ohlcv_from_symbol


st.title("Load Yahoo Finance data")

# Upload JSON
uploaded_files = st.file_uploader("Choose one or more Yahoo Finance JSON files", 
                                  type="json", accept_multiple_files=True)

for uploaded_file in uploaded_files:

    try:
            
        parser = YahooSymbolParser(uploaded_file.name)
        load_ohlcv_from_symbol(parser.symbol)

    except Exception as e:

        st.error(f"Failed to load file: {uploaded_file.name}")
        print(e)
