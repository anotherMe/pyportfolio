
from datetime import datetime
import json
import logging
import yfinance as yf
from typing import Any, Tuple

from lib.database import get_session
from lib.models import Instrument
from lib.repo.instruments_repository import get_instrument_by_ticker
from lib.repo.ohlcvs_repository import load_ohlcv_from_symbol, load_ohlcv_from_yfinance_dataframe
from lib.repo.prices_repository import load_prices_from_symbol, load_prices_from_yfinance_dataframe
from service.custom_exceptions import PortfolioException
from service.myYahooFinanceService import YahooSymbolParser

from logging_config import setup_logger
log = setup_logger(__name__)

DEFAULT_GRANULARITY = '1d'


def download_history(instrument: Instrument, start_date: datetime) -> Tuple[bool, str]:

    try:
        yf_symbol = yf.Ticker(instrument.ticker)
        df = yf_symbol.history(start=start_date, interval=DEFAULT_GRANULARITY)
        load_ohlcv_from_yfinance_dataframe(df, DEFAULT_GRANULARITY, instrument)
        load_prices_from_yfinance_dataframe(df, DEFAULT_GRANULARITY, instrument)
        return True, f"Symbol {instrument.ticker} parsed correctly"
    
    except Exception:
        logging.exception("")
        return(False, f"Failed to parse symbol: {instrument.ticker}")


def parse_json_file_into_yahoo_symbol(uploaded_file: Any) -> YahooSymbolParser:
    try:
        data = json.load(uploaded_file)
        return YahooSymbolParser(data)
    except Exception:
        logging.exception("")
        raise PortfolioException("YahooFinanceService", f"Failed to parse file: {uploaded_file.name}")


def parse_file(parser: YahooSymbolParser, create_instrument: bool):
    """For each uploaded file: 

        - parse the JSON into a YahooSymbolParser object
        - retrieve the Instrument if present ...
        - create the Instrument if not present
        - load Prices
        - load OHLCVs

    Args:
        uploaded_file (Any): _description_
        create_instrument (bool): _description_

    Raises:
        PortfolioException: _description_
    """

    with get_session() as session:
        try:
            instrument = get_instrument_by_ticker(session, parser.symbol.ticker)
        except Exception as ex:
            print(ex)
            raise PortfolioException("YahooFinanceService", f"Error while retrieving Instrument with ticker {parser.symbol.ticker}")
            
    if not instrument and not create_instrument:
        raise PortfolioException("YahooFinanceService", f"No Instrument found with ticker: {parser.symbol.ticker}")

    if not instrument and create_instrument:

        with get_session() as session:
            try:
                instrument = Instrument()
                instrument.ticker = parser.symbol.ticker
                instrument.name = parser.symbol.name
                instrument.name_long = parser.symbol.long_name
                instrument.currency = parser.symbol.currency
                session.add(instrument)
                session.commit()
            except Exception as ex:
                session.rollback()
                logging.exception()
                raise PortfolioException("YahooFinanceService", "Error while parsing file") from ex
                
    try:
        load_ohlcv_from_symbol(parser.symbol, parser.symbol.data_granularity, instrument)
    except Exception as ex:
        logging.exception()
        raise PortfolioException("YahooFinanceService", "Can't load data into OHLCVs") from ex
    
    try:
        load_prices_from_symbol(parser.symbol, parser.symbol.data_granularity, instrument)
    except Exception as ex:
        logging.exception()
        raise PortfolioException("YahooFinanceService", "Can't load data into Prices") from ex