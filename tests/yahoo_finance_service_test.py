
from unittest.mock import MagicMock, patch
from datetime import datetime

from lib.database import get_session
from lib.models import Instrument
from service.YahooFinanceService import (
    download_history,
    DEFAULT_GRANULARITY,
)


def test_download_history():
    
    with get_session() as session, session.begin():
        i:Instrument = session.query(Instrument).filter_by(ticker='NATO.MI',).first()
        start_date = datetime.now()
        download_history(i, start_date)


@patch("yfinance.Ticker")
@patch("lib.repo.ohlcvs_repository.load_ohlcv_from_yfinance_dataframe")
@patch("lib.repo.prices_repository.load_prices_from_yfinance_dataframe")
def test_download_history_success(mock_load_prices, mock_load_ohlcv, mock_ticker):

    mock_df = MagicMock()
    mock_ticker.return_value.history.return_value = mock_df

    instrument = MagicMock(ticker="AAPL")

    ok, msg = download_history(instrument, datetime(2020, 1, 1))

    assert ok is True
    assert "AAPL" in msg
    mock_ticker.assert_called_once_with("AAPL")
    mock_ticker.return_value.history.assert_called_once()
    mock_load_ohlcv.assert_called_once_with(mock_df, DEFAULT_GRANULARITY, instrument)
    mock_load_prices.assert_called_once_with(mock_df, DEFAULT_GRANULARITY, instrument)


@patch("yfinance.Ticker", side_effect=Exception("boom"))
def test_download_history_failure(mock_ticker):
    instrument = MagicMock(ticker="AAPL")
    ok, msg = download_history(instrument, datetime(2020, 1, 1))

    assert ok is False
    assert "AAPL" in msg
