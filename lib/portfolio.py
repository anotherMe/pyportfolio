from lib.db import (
    get_session,
    init_db,
    add_instrument,
    get_instrument_by_isin,
    add_trade,
    add_market_price,
    add_transaction,
    get_portfolio_value,
    get_position
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
    session = get_session()
    instruments = session.query(get_instrument_by_isin(session).__class__).all()
    print(f"{'Ticker':<10}{'Qty':>6}{'Avg Price':>12}{'Last Price':>12}{'Value':>12}")
    print("-"*52)
    for inst in instruments:
        qty, avg_price = get_position(session, inst.id)
        if qty <= 0:
            continue
        last_price_obj = session.query(inst.prices).order_by(-inst.prices[-1].date).first()
        last_price = last_price_obj.price / 100 if last_price_obj else 0
        value = qty * last_price
        print(f"{inst.ticker or inst.name:<10}{qty:>6}{avg_price:>12.2f}{last_price:>12.2f}{value:>12.2f}")
