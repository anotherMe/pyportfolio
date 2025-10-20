
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from lib.database import save_to_db, read_from_db
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
    print(f"📊 Portfolio value (including global transactions): {read_from_db(total_cents):.2f}")
    return read_from_db(total_cents)


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
    total_cost = read_from_db(sum(q * p for q, p in inventory))
    return total_cost / total_qty if total_qty > 0 else 0.0

def compute_pnl_for_sells(session: Session):
    """Compute average buy price and PnL for all sell trades."""
    
    sell_trades = session.scalars(select(Trade).where(Trade.type == "sell").order_by(Trade.date)).all()

    results = []
    for sell in sell_trades:
        # --- get all previous buys for same instrument ---
        buys = session.scalars(
            select(Trade)
            .where(
                Trade.instrument_id == sell.instrument_id,
                Trade.type == "buy",
                Trade.date < sell.date
            )
            .order_by(Trade.date)
        ).all()

        if not buys:
            results.append({
                "trade": sell,
                "avg_buy_price": None,
                "pnl": None
            })
            continue

        # --- compute weighted average buy price ---
        total_qty = sum(b.quantity for b in buys)
        avg_buy_price = sum(b.quantity * b.price for b in buys) / total_qty

        # --- compute PnL ---
        pnl = (sell.price - avg_buy_price) * sell.quantity

        results.append({
            "trade": sell,
            "avg_buy_price": avg_buy_price,
            "pnl": pnl
        })

    return results


def compute_fifo_pnl(session: Session):
    """Compute FIFO-based average buy price and realized PnL for all sell trades."""

    results = []

    # get all instruments
    instruments = session.execute(select(Trade.instrument_id).distinct()).scalars().all()

    for inst_id in instruments:
        # sort trades for this instrument by date
        trades = session.scalars(
            select(Trade)
            .where(Trade.instrument_id == inst_id)
            .order_by(Trade.date)
        ).all()

        # --- maintain FIFO buy queue ---
        buy_queue = []  # list of dicts: {"remaining_qty": float, "price": float}

        for t in trades:
            if t.type == "buy":
                buy_queue.append({"remaining_qty": t.quantity, "price": t.price})
                continue

            if t.type == "sell":
                sell_qty = t.quantity
                realized_pnl = 0.0
                matched_qty = 0.0

                # match FIFO
                while sell_qty > 0 and buy_queue:
                    lot = buy_queue[0]
                    take_qty = min(sell_qty, lot["remaining_qty"])
                    cost_price = lot["price"]

                    realized_pnl += (t.price - cost_price) * take_qty
                    matched_qty += take_qty

                    # update remaining quantities
                    lot["remaining_qty"] -= take_qty
                    sell_qty -= take_qty

                    # remove depleted lots
                    if lot["remaining_qty"] <= 0:
                        buy_queue.pop(0)

                avg_buy_price = (t.price - (realized_pnl / matched_qty)) if matched_qty else None

                results.append({
                    "trade": t,
                    "avg_buy_price": avg_buy_price,
                    "pnl": realized_pnl if matched_qty else None,
                })

    return results
