
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from lib.database import get_session
from service.accounts_service import AccountsService
from service.ohlcvs_service import OhlcvsService
from service.positions_service import PositionsService


# ----------------------------------------------------------------------------------------------------------------------
# retrieve base data

_accounts_service = AccountsService()
_positions_service = PositionsService()
_ohlcvs_service = OhlcvsService()

with get_session() as session:
    current_account = _accounts_service.get_by_name(session, st.session_state.account)
    account_id = current_account.id if current_account else 0
    positions_df = _positions_service.get_summary(session, account_id=account_id, include_closed=False, include_open=True)
    prices_list = _ohlcvs_service.get_prices_for_instrument(session, 12)

total_portfolio = (positions_df["latest_price"] * positions_df["remaining_quantity"]).sum()
positions_df["percent"] = total_portfolio / ( positions_df["latest_price"] * positions_df["remaining_quantity"] )
prices_df = pd.DataFrame([p.model_dump(mode="json") for p in prices_list])


# ----------------------------------------------------------------------------------------------------------------------
# page layout

st.set_page_config(page_title="Dashboard")
st.title("Dashboard")

tab1, tab2 = st.tabs(["one", "two"])

with tab1:
    col1, col2 = st.columns(2)
    with col1:
        fig = px.pie(positions_df, values="percent", names="instrument_asset_class")
        st.plotly_chart(fig, key="asset_pie_chart", config = {'scrollZoom': False})
    with col2:
        fig = px.pie(positions_df, values="percent", names="instrument_name")
        st.plotly_chart(fig, key="instrument_pie_chart", config = {'scrollZoom': False})
            
with tab2:
    fig = go.Figure(data=go.Ohlc(x=prices_df['date'],
                    open=prices_df['open'],
                    high=prices_df['high'],
                    low=prices_df['low'],
                    close=prices_df['close']))
    st.plotly_chart(fig, key="instrument_line_chart")
    st.empty()
