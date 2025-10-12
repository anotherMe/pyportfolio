from rich.table import Table
from rich.console import Console
from lib.db import (
    get_all_instruments,
    get_latest_market_price,
    get_session,
    init_db,
    add_instrument,
    get_instrument_by_isin,
    add_trade,
    add_market_price,
    add_transaction,
    get_portfolio_value,
    get_position,
)


def handle_init_db():
    init_db()

def handle_add_instrument(args):
    session = get_session()
    add_instrument(session, args.isin, args.name, args.ticker, args.category, args.currency)

def handle_trade(args):
    session = get_session()
    inst = get_instrument_by_isin(session, args.isin)
    if not inst:
        print(f"❌ Instrument with ISIN {args.isin} not found.")
        return
    add_trade(session, inst, args.command, int(args.qty), args.price, args.fees, args.description)

def handle_transaction(args):
    session = get_session()
    inst = get_instrument_by_isin(session, args.isin) if args.isin else None
    if args.isin and not inst:
        print(f"❌ Instrument with ISIN {args.isin} not found.")
        return
    add_transaction(session, args.type, args.amount, inst, args.description)

def handle_add_price(args):
    session = get_session()
    inst = get_instrument_by_isin(session, args.isin)
    if not inst:
        print(f"❌ Instrument with ISIN {args.isin} not found.")
        return
    add_market_price(session, inst, args.price)

def handle_portfolio_value(args):
    session = get_session()
    get_portfolio_value(session)


def handle_show_positions(args):
    console = Console()
    session = get_session()
    instruments = get_all_instruments(session)

    if not instruments:
        console.print("[yellow]⚠️ No instruments found in the database.[/yellow]")
        return

    table = Table(title="📊 Portfolio Positions")
    table.add_column("Ticker", justify="left", style="cyan", no_wrap=True)
    table.add_column("Qty", justify="right")
    table.add_column("Avg Price", justify="right")
    table.add_column("Last Price", justify="right")
    table.add_column("Value", justify="right", style="green")

    total_value = 0.0

    for inst in instruments:
        qty, avg_price = get_position(session, inst.id)
        if qty <= 0:
            continue

        last_price = get_latest_market_price(session, inst.id) or 0.0
        value = qty * last_price
        total_value += value

        table.add_row(
            inst.ticker or inst.name,
            str(qty),
            f"{avg_price:.2f} {inst.currency}",
            f"{last_price:.2f} {inst.currency}",
            f"{value:.2f} {inst.currency}",
        )

    console.print(table)
    console.print(f"\n💰 [bold green]Total portfolio value:[/bold green] {total_value:.2f} EUR")  # FIXME: how to manage currency here ?

