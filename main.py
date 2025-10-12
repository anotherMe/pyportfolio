import argparse
import portfolio as pf

def main():
    parser = argparse.ArgumentParser(description="📊 Portfolio Manager CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # init-db
    subparsers.add_parser("init-db", help="Initialize the database")

    # add-instrument
    p_add = subparsers.add_parser("add-instrument", help="Add a new instrument")
    p_add.add_argument("--isin", required=True)
    p_add.add_argument("--name", required=True)
    p_add.add_argument("--ticker")
    p_add.add_argument("--category")
    p_add.add_argument("--currency", default="EUR")

    # buy / sell
    for cmd in ["buy", "sell"]:
        p_trade = subparsers.add_parser(cmd, help=f"Record a {cmd} trade")
        p_trade.add_argument("--isin", required=True)
        p_trade.add_argument("--qty", type=int, required=True)
        p_trade.add_argument("--price", type=float, required=True)
        p_trade.add_argument("--fees", type=float, default=0.0)
        p_trade.add_argument("--description")

    # add-transaction
    p_trans = subparsers.add_parser("add-transaction", help="Add a tax/dividend/fee")
    p_trans.add_argument("--type", required=True, choices=["dividend", "tax", "fee", "global_tax"])
    p_trans.add_argument("--amount", type=float, required=True)
    p_trans.add_argument("--isin")
    p_trans.add_argument("--description")

    # add-price
    p_price = subparsers.add_parser("add-price", help="Add a market price")
    p_price.add_argument("--isin", required=True)
    p_price.add_argument("--price", type=float, required=True)

    # portfolio-value
    subparsers.add_parser("portfolio-value", help="Compute portfolio value")

    # show-positions
    subparsers.add_parser("show-positions", help="Show current positions")

    args = parser.parse_args()

    match args.command:
        case "init-db":
            pf.handle_init_db()
        case "add-instrument":
            pf.handle_add_instrument(args)
        case "buy" | "sell":
            pf.handle_trade(args)
        case "add-transaction":
            pf.handle_transaction(args)
        case "add-price":
            pf.handle_add_price(args)
        case "portfolio-value":
            pf.handle_portfolio_value(args)
        case "show-positions":
            pf.handle_show_positions(args)

if __name__ == "__main__":
    main()
