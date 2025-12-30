
from typing import Optional
from attr import dataclass
import pandas as pd
from sqlalchemy import func, select, text
from lib.database import read_from_db
from lib.models import Instrument, Trade, Transaction, UTCDateTime
from lib.repo.prices_repository import get_latest_price

from lib.repo.trades_repository import get_all_trades
from logging_config import setup_logger
log = setup_logger(__name__)


# -----------------------
# -- Models
# -----------------------

@dataclass
class Position:
    instrument: Optional[Instrument] = None
    type: str = "open"          # 'open' or 'closed'
    quantity: int = 0
    buy_price: float = 0
    pnl: float = 0
    pnl_percent: float = 0.00
    closing_price: float = 0      # latest market price or closing price
    closing_date: Optional[UTCDateTime] = None


# ----------------------------
# 🔹 Utility functions
# ----------------------------

def _get_instruments_with_trades(session, account=None):
    """Return list of Instruments that have at least one trade."""

    if account:
        stmt = select(Instrument).where(
            Instrument.id.in_(
                select(Trade.instrument_id).where(Trade.account_id == account.id)
            )
        )
    else:
        stmt = select(Instrument).where(
            Instrument.id.in_(
                select(Trade.instrument_id)
            )
        )

    return session.scalars(stmt).all()


# def _get_trades_for_instrument(session, instrument, account=None):
#     """Return ordered trades for an instrument."""
#     stmt = (
#         select(Trade)
#         .where(Trade.instrument_id == instrument.id)
#         .order_by(Trade.date)
#     )
#     if account:
#         stmt = stmt.where(Trade.account_id == account.id)
#     return session.scalars(stmt).all()

# def _get_transactions_totals_for_trade(session, trade_id, account=None):
#     """Return sum of transactions amounts, grouped by Trade."""

#     stmt = (
#         session.query(
#             Transaction.trade_id,
#             func.sum(Transaction.amount).label("amount_total")
#         )
#         .filter(Transaction.trade_id == trade_id)
#         .group_by(Transaction.trade_id)
#     )

#     if account:
#         stmt = stmt.where(Trade.account_id == account.id)

#     return stmt.all()

def _apply_fifo(session, account):
    """
    Apply FIFO to trades of the same Instrument
    Returns:
        closed_trades: list of dicts with realized PnL
        open_lots: remaining open lots (list of dicts)
    """

    all_trades = get_all_trades(session, account)
    positions = []

    for instrument in _get_instruments_with_trades(session, account):

        buy_queue = []
        trades = [trade for trade in all_trades if trade.instrument_id == instrument.id]

        for t in trades:

            if t.type == "buy":
                buy_queue.append({"trade": t, "remaining_qty": t.quantity, "price": t.price})
            elif t.type == "sell":
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

                    lot["remaining_qty"] -= take_qty
                    sell_qty -= take_qty
                    if lot["remaining_qty"] <= 0:
                        buy_queue.pop(0)

                if matched_qty > 0:
                    avg_buy_price = (t.price - (realized_pnl / matched_qty))  # TODO: check this
                    position = Position()
                    position.instrument = instrument
                    position.type = 'closed'
                    position.quantity = matched_qty
                    position.buy_price = read_from_db(avg_buy_price)
                    position.pnl = read_from_db(realized_pnl)
                    position.pnl_percent = ( read_from_db(t.price) - read_from_db(avg_buy_price) ) / read_from_db(avg_buy_price)
                    position.closing_price = read_from_db(t.price)
                    position.closing_date = t.date
                    positions.append(position)

        if len(buy_queue) > 0:

            total_qty = sum(l["remaining_qty"] for l in buy_queue)
            total_cost = sum(l["remaining_qty"] * l["price"] for l in buy_queue)
            avg_cost = total_cost / total_qty

            latest_price = get_latest_price(session, instrument.id)
            unrealized_pnl = (
                (latest_price - avg_cost) * total_qty
                if latest_price is not None and avg_cost is not None
                else None
            )

            position = Position()
            position.instrument = instrument
            position.type = 'open'
            position.quantity = total_qty
            position.buy_price = read_from_db(avg_cost)
            position.pnl = read_from_db(unrealized_pnl)
            position.pnl_percent = ( read_from_db(latest_price) - read_from_db(avg_cost) ) / read_from_db(avg_cost)
            position.closing_price = read_from_db(latest_price)
            position.closing_date = None
            positions.append(position)

    return positions


# ----------------------------
# 🔸 Public API
# ----------------------------

def get_positions_summary(session, account=None, include_closed=True, include_open=True):
    """
    Combine closed and open positions into a single unified summary.

    Returns a list of dicts (or DataFrame) with standardized keys:
        instrument, instrument_id, type, quantity, avg_price, 
        market_price, pnl, pnl_type ('realized' or 'unrealized')
    """

    all_positions = _apply_fifo(session, account)
    filtered_positions = []
    pos: Position
    for pos in all_positions:

        if  pos.type == 'closed' and include_closed:
            filtered_positions.append(pos)

        if pos.type == 'open' and include_open:
            filtered_positions.append(pos)


    # Return a pandas DataFrame for easy integration with Streamlit
    df = pd.DataFrame([vars(p) for p in filtered_positions])
    # for some reason, int types get converted to float64 dtypes -> need to fix it
    df['quantity'] = df['quantity'].astype('Int64')

    # insert column for instrument name ( inserting it at first position )
    df.insert(0, "instrument_name", df["instrument"].apply(lambda inst: inst.name))

    # Optional: sort and format
    if not df.empty:
        # df = df.sort_values(by=["instrument_id", "type", "closing_date"], ascending=[True, True, True])
        df = df.sort_values(by=["closing_date"], ascending=[True])
        df.reset_index(drop=True, inplace=True)

    return df


# def compute_closed_positions(session, account=None):
#     """Compute FIFO-based realized PnL for all instruments (closed positions)."""
#     results = []

#     for inst_id in _get_instruments_with_trades(session, account):
#         trades = _get_trades_for_instrument(session, inst_id, account)
#         closed_trades, _ = _apply_fifo(trades)
#         results.extend(closed_trades)

#     return results


# def compute_open_positions(session, account=None):
#     """Compute open positions (unrealized PnL) using FIFO."""
#     results = []

#     for inst_id in _get_instruments_with_trades(session, account):
#         trades = _get_trades_for_instrument(session, inst_id, account)
#         _, open_lots = _apply_fifo(trades)
        
#         if not open_lots:
#             continue

#         total_qty = sum(l["remaining_qty"] for l in open_lots)
#         total_cost = sum(l["remaining_qty"] * l["price"] for l in open_lots)
#         avg_cost = total_cost / total_qty if total_qty else None

#         latest_price = get_latest_price(session, inst_id)
#         unrealized_pnl = (
#             (latest_price - avg_cost) * total_qty
#             if latest_price is not None and avg_cost is not None
#             else None
#         )

#         instrument = session.get(Instrument, inst_id)

#         results.append({
#             "instrument": instrument,
#             "instrument_id": inst_id,
#             "quantity": total_qty,
#             "avg_cost": avg_cost,
#             "latest_price": latest_price,
#             "unrealized_pnl": unrealized_pnl,
#         })

#     return results


# --------------------------------------------------------------------------------------------------------
# older function definitions

def get_portfolio_value(session):
    total_cents = 0
    instruments = session.query(Instrument).all()
    for inst in instruments:
        qty, _ = get_position(session, inst.id)
        if qty <= 0:
            continue
        last_price = get_latest_price(session)
        if last_price:
            total_cents += qty * last_price[0]

    global_cash = session.query(func.sum(Transaction.amount)).filter(Transaction.instrument_id.is_(None)).scalar() or 0
    total_cents += global_cash
    log.info(f"📊 Portfolio value (including global transactions): {read_from_db(total_cents):.2f}")
    return read_from_db(total_cents)

def get_position(session, instrument_id):
    net_qty = get_current_quantity(session, instrument_id)
    if net_qty <= 0:
        return 0, 0.0

    avg_price = get_average_buy_price(session, instrument_id)
    return net_qty, avg_price


def get_open_positions(session, account=None):

    # Get trades
    trades = []
    if account:
        trades = session.query(Trade).filter_by(account_id=account.id).all()
    else:
        trades = session.query(Trade).all()

    # Convert to DataFrame for easier grouping
    df = pd.DataFrame([{
        "instrument_id": t.instrument_id,
        "type": t.type.upper(),
        "qty": t.quantity,
        "price": read_from_db(t.price)
    } for t in trades])

    if df.empty:
        return pd.DataFrame()

    # Compute net quantity and weighted average cost
    grouped = df.groupby("instrument_id").apply(lambda x: pd.Series({
        "total_buys": (x.loc[x.type == "BUY", "qty"].sum()),
        "total_sells": (x.loc[x.type == "SELL", "qty"].sum()),
        "net_qty": (x.loc[x.type == "BUY", "qty"].sum() - x.loc[x.type == "SELL", "qty"].sum()),
        "avg_buy_price": (
            (x.loc[x.type == "BUY", "qty"] * x.loc[x.type == "BUY", "price"]).sum() /
            x.loc[x.type == "BUY", "qty"].sum()
        ) if (x.loc[x.type == "BUY", "qty"].sum() > 0) else None,
    })).reset_index()

    # Filter only open positions
    grouped = grouped[grouped.net_qty != 0]

    # Optionally join instrument names
    instruments = session.query(Instrument).all()
    id_to_name = {i.id: i.name for i in instruments}
    grouped["instrument"] = grouped.instrument_id.map(id_to_name)

    # Reorder columns
    grouped = grouped[["instrument", "net_qty", "avg_buy_price"]]
    grouped["avg_buy_price"] = grouped["avg_buy_price"].round(2)
    return grouped


def get_all_positions(session, account=None):

    if account:
        query = text("""
                select 
                    instruments.name, 
                    sum(case when type = 'buy' then -price else price end * quantity) as value, 
                    sum(case when type = 'buy' then quantity else -quantity end) as qty_left
                from trades
                inner join instruments on instruments.id = trades.instrument_id
                where account_id = :account_id
                group by instruments.name;
            """)
    else:
        query = text("""
                select 
                    instruments.name, 
                    sum(case when type = 'buy' then -price else price end * quantity) as value, 
                    sum(case when type = 'buy' then quantity else -quantity end) as qty_left
                from trades
                inner join instruments on instruments.id = trades.instrument_id
                group by instruments.name;
            """)


    if account:
        result = session.execute(query, {"account_id": account.id})
    else:
        result = session.execute(query)

    rows = result.all()

    # Convert to DataFrame for easier grouping
    df = pd.DataFrame([{
        "instrument": row.name,
        "quantity": row.qty_left,
        "value": read_from_db(row.value),
    } for row in rows])

    if df.empty:
        return pd.DataFrame()
    else:
        return df

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

