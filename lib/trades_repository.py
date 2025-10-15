
from sqlalchemy import func
from datetime import datetime
from lib.database import to_cents, from_cents
from lib.models import Trade

def add_trade(session, instrument, trade_type, quantity, price, fees, tax_rate, description=None):
    
    trade = Trade(
        instrument_id=instrument.id,
        date=datetime.now(),
        type=trade_type,
        quantity=int(quantity),
        price=to_cents(price),
        description=description,
    )
    session.add(trade)
    session.flush()  # ensures IDs and defaults are populated

    print(f"📈 Recorded trade: {trade_type.upper()} {quantity}x {instrument.ticker or instrument.name} @ {price:.2f}")

    return trade

def delete_trade(session, trade_id):
    trade = session.get(Trade, trade_id)
    if trade:
        session.delete(trade)
        session.flush()
        print(f"🗑️ Deleted trade ID {trade_id}")
        return True
    else:
        print(f"❌ Trade ID {trade_id} not found.")
        return False

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