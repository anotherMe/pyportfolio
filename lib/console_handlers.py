
from lib.database import init_db
from lib.myYahooFinance import YahooSymbolParser
from lib.portfolio_repository import load_market_prices_from_symbol


def handle_init_db():
    init_db()

def handle_load_data(args):

    parser = YahooSymbolParser(args.file)
    if parser.symbol:
        load_market_prices_from_symbol(parser.symbol)
    else:
        print("No symbol present")

