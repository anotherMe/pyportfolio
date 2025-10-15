
from sqlalchemy import func
from lib.database import to_cents, from_cents
from lib.models import Instrument, MarketPrice, Transaction
from lib.trades_repository import get_current_quantity, get_average_buy_price


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

    avg_price_cents = get_average_buy_price(session, instrument_id)
    return net_qty, avg_price_cents