
from datetime import datetime, timedelta
import json
import logging
from lib.database import get_session, init_db
from lib.models import Instrument
from service.YahooFinanceService import download_history
from service.myYahooFinanceService import YahooSymbolParser
from lib.repo.ohlcvs_repository import load_ohlcv_from_symbol
from lib.repo.prices_repository import load_prices_from_symbol


logger = logging.getLogger(__name__)


def handle_init_db():
    init_db()

def handle_load_json(args):

    try:
        with open(args.file, mode="r", encoding="utf-8") as read_file:
            data = json.load(read_file)        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return
    except (ValueError, IndexError) as e:
        logger.error(f"Error parsing JSON: {e}")
        return

    try:
        parser = YahooSymbolParser(data)
        load_ohlcv_from_symbol(parser.symbol, True) # FIXME: this boolean parameter should not be fixed in code
        load_prices_from_symbol(parser.symbol, True) # FIXME: this boolean parameter should not be fixed in code
    except Exception as ex:
        logger.error("Error while trying to load market prices / OHLCVs")
        logger.error(ex)

def handle_load_ticker(args):

    try:
        with get_session() as session, session.begin():
            instrument:Instrument = session.query(Instrument).where(Instrument.ticker==args.ticker).first()
            success, message = download_history(instrument, datetime.now() - timedelta(days=int(args.days))) 
            if success:
                logger.info(message)
            else:
                logger.error(message)

            return True, f"Symbol {instrument.ticker} parsed correctly"
    except Exception as ex:
        logger.error(f"Error while trying to load prices for {args.ticker}")
        logger.error(ex)
        return
