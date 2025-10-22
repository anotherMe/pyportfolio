
import json
import logging
from lib.database import init_db
from lib.myYahooFinance import YahooSymbolParser
from lib.repo.portfolio_repository import load_market_prices_from_symbol, load_ohlcv_from_symbol

logger = logging.getLogger(__name__)


def handle_init_db():
    init_db()

def handle_load_data(args):

    # --- Load file and parse it into JSON data
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
        load_market_prices_from_symbol(parser.symbol)
        load_ohlcv_from_symbol(parser.symbol)
    except Exception as ex:
        logger.error("Error while trying to load market prices / OHLCVs")
        logger.error(ex)