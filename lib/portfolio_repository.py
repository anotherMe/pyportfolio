
from sqlalchemy import func
from lib.database import to_cents, from_cents
from lib.models import Instrument, MarketPrice, Trade, Transaction


def get_portfolio_value(session):
    total_cents = 0
    instruments = session.query(Instrument).all()
    for inst in instruments:
        qty, _ = get_position(session, inst.id)
        if qty <= 0:
            continue
        last_price = session.query(MarketPrice.price).filter_by(instrument_id=inst.id).order_by(MarketPrice.date.desc()).first()
        if last_price:
            total_cents += qty * last_price[0]

    global_cash = session.query(func.sum(Transaction.amount)).filter(Transaction.instrument_id.is_(None)).scalar() or 0
    total_cents += global_cash
    print(f"📊 Portfolio value (including global transactions): {from_cents(total_cents):.2f}")
    return from_cents(total_cents)


def get_position(session, instrument_id):
    net_qty = get_current_quantity(session, instrument_id)
    if net_qty <= 0:
        return 0, 0.0

    avg_price = get_average_buy_price(session, instrument_id)
    return net_qty, avg_price


def get_current_quantity(session, instrument_id):
    buys = (
        session.query(Trade)
        .filter(Trade.instrument_id == instrument_id, Trade.type == "buy")
        .with_entities(func.sum(Trade.quantity))
        .scalar() or 0.0
    )
    sells = (
        session.query(Trade)
        .filter(Trade.instrument_id == instrument_id, Trade.type == "sell")
        .with_entities(func.sum(Trade.quantity))
        .scalar() or 0.0
    )
    return buys - sells


def get_average_buy_price(session, instrument_id):
    """
    Compute FIFO-based average buy price for the currently owned quantity of an instrument.
    """

    # Retrieve trades in chronological order
    trades = (
        session.query(Trade)
        .filter(Trade.instrument_id == instrument_id)
        .order_by(Trade.date)
        .all()
    )

    inventory = []  # list of [qty_remaining, price_per_unit]
    for trade in trades:
        if trade.type == "buy":
            inventory.append([trade.quantity, trade.price])
        elif trade.type == "sell":
            qty_to_sell = trade.quantity
            while qty_to_sell > 0 and inventory:
                first_lot = inventory[0]
                if first_lot[0] <= qty_to_sell:
                    qty_to_sell -= first_lot[0]
                    inventory.pop(0)
                else:
                    first_lot[0] -= qty_to_sell
                    qty_to_sell = 0

    total_qty = sum(q for q, _ in inventory)
    total_cost = from_cents(sum(q * p for q, p in inventory))
    return total_cost / total_qty if total_qty > 0 else 0.0