import streamlit as st

from lib.myYahooFinance import YahooSymbolParser


st.title("Test page")

parser = YahooSymbolParser("data/IEGE.MI.json")
if parser.symbol:
    st.write(f"Loaded symbol: {parser.symbol.name}")
    st.dataframe(parser.symbol.ochlv_df)