
import argparse
import lib.console_handlers as c

def main():
    parser = argparse.ArgumentParser(description="📊 Portfolio Manager CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # init-db
    subparsers.add_parser("init-db", help="Initialize the database")

    # add-instrument
    p_add = subparsers.add_parser("add-instrument", help="Add a new instrument")
    p_add.add_argument("-i", "--isin", required=True)
    p_add.add_argument("-n", "--name", required=True)
    p_add.add_argument("-t", "--ticker")
    p_add.add_argument("-c", "--category")
    p_add.add_argument("-cur", "--currency", default="EUR")

    # buy / sell
    for cmd in ["buy", "sell"]:
        p_trade = subparsers.add_parser(cmd, help=f"Record a {cmd} trade")
        p_trade.add_argument("-i", "--isin", required=True)
        p_trade.add_argument("-q", "--qty", type=int, required=True)
        p_trade.add_argument("-p", "--price", type=float, required=True, help="Price per unit")
        p_trade.add_argument("-f", "--fees", type=float, default=39.0, help="Total fees for the trade (default: 39.0 €)")
        p_trade.add_argument("-tr", "--tax_rate", type=float, default=26.0, help="Tax rate in % (default: 26%)")
        p_trade.add_argument("--description")

    # add-transaction
    p_trans = subparsers.add_parser("add-transaction", help="Add a tax/dividend/fee")
    p_trans.add_argument("-t", "--type", required=True, choices=["dividend", "tax", "fee", "global_tax"])
    p_trans.add_argument("-a", "--amount", type=float, required=True)
    p_trans.add_argument("-i", "--isin")
    p_trans.add_argument("-d", "--description")

    # add-price
    p_price = subparsers.add_parser("add-price", help="Add a market price")
    p_price.add_argument("-i", "--isin", required=True)
    p_price.add_argument("-p", "--price", type=float, required=True)

    # portfolio-value
    subparsers.add_parser("portfolio-value", help="Compute portfolio value")

    # show-positions
    subparsers.add_parser("show-positions", help="Show current positions")

    args = parser.parse_args()

    match args.command:
        case "init-db":
            c.handle_init_db()
        case "add-instrument":
            c.handle_add_instrument(args)
        case "buy" | "sell":
            c.handle_trade(args)
        case "add-transaction":
            c.handle_transaction(args)
        case "add-price":
            c.handle_add_price(args)
        case "portfolio-value":
            c.handle_portfolio_value(args)
        case "show-positions":
            c.handle_show_positions(args)

if __name__ == "__main__":
    main()
