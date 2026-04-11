
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from lib.database import get_session
from service.accounts_service import AccountsService
from service.positions_service import PositionsService


# ----------------------------------------------------------------------------------------------------------------------
# retrieve base data

_accounts_service = AccountsService()
_positions_service = PositionsService()

with get_session() as session:
    current_account = _accounts_service.get_by_name(session, st.session_state.account)
    account_id = current_account.id if current_account else 0
    positions_df = _positions_service.get_summary(session, account_id=account_id, include_closed=False, include_open=True)

total_portfolio = (positions_df["latest_price"] * positions_df["remaining_quantity"]).sum()
positions_df["percent"] = total_portfolio / ( positions_df["latest_price"] * positions_df["remaining_quantity"] )


# ----------------------------------------------------------------------------------------------------------------------
# page layout

st.set_page_config(page_title="Dashboard")
st.title("Dashboard")

tab1, tab2 = st.tabs(["Allocation by asset class", "Allocation by instrument"])

with tab1:
    fig = px.pie(positions_df, values="percent", names="instrument_asset_class")
    st.plotly_chart(fig, key="asset_pie_chart", config = {'scrollZoom': False})
with tab2:
    fig = px.pie(positions_df, values="percent", names="instrument_name")
    st.plotly_chart(fig, key="instrument_pie_chart", config = {'scrollZoom': False})
        