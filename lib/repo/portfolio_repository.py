
from narwhals import Boolean
import pandas as pd
from sqlalchemy import func, select, text
from lib.database import get_session, read_from_db
from lib.models import Instrument, OHLCV, Trade, Transaction
from sqlalchemy.exc import IntegrityError
from lib.database import write_to_db
from lib.myYahooFinance import Symbol


# ----------------------------
# 🔹 Utility functions
# ----------------------------


def _get_instruments_with_trades(session, account=None):
    """Return list of instrument IDs that have trades."""
    stmt = select(Trade.instrument_id).distinct()
    if account:
        stmt = stmt.where(Trade.account_id == account.id)
    return session.scalars(stmt).all()


def _get_trades_for_instrument(session, inst_id, account=None):
    """Return ordered trades for an instrument."""
    stmt = (
        select(Trade)
        .where(Trade.instrument_id == inst_id)
        .order_by(Trade.date)
    )
    if account:
        stmt = stmt.where(Trade.account_id == account.id)
    return session.scalars(stmt).all()


def _apply_fifo(trades):
    """
    Apply FIFO to a sequence of trades.
    Returns:
        closed_trades: list of dicts with realized PnL
        open_lots: remaining open lots (list of dicts)
    """
    buy_queue = []
    closed_trades = []

    for t in trades:
        if t.type == "buy":
            buy_queue.append({"remaining_qty": t.quantity, "price": t.price})
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
                avg_buy_price = (t.price - (realized_pnl / matched_qty))
                closed_trades.append({
                    "trade": t,
                    "avg_buy_price": avg_buy_price,
                    "pnl": realized_pnl,
                })

    return closed_trades, buy_queue


def _get_latest_market_price(session, inst_id):
    """Return the latest market price for an instrument, or None."""
    stmt = (
        select(OHLCV.close)
        .where(OHLCV.instrument_id == inst_id)
        .order_by(OHLCV.timestamp.desc())
        .limit(1)
    )
    return session.scalar(stmt)


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

    results = []

    if include_closed:
        closed_positions = compute_closed_positions(session, account)
        for pos in closed_positions:
            trade = pos["trade"]
            instrument = trade.instrument
            results.append({
                "instrument": instrument.name if instrument else None,
                "instrument_id": trade.instrument_id,
                "type": "closed",
                "date": trade.date,
                "quantity": trade.quantity,
                "avg_price": read_from_db(pos["avg_buy_price"]),
                "market_price": read_from_db(trade.price),  # execution price
                "pnl": read_from_db(pos["pnl"]),
            })

    if include_open:
        open_positions = compute_open_positions(session, account)
        for pos in open_positions:
            instrument = pos["instrument"]
            results.append({
                "instrument": instrument.name if instrument else None,
                "instrument_id": pos["instrument_id"],
                "type": "open",
                "date": None,
                "quantity": pos["quantity"],
                "avg_price": read_from_db(pos["avg_cost"]),
                "market_price": read_from_db(pos["latest_price"]) if pos["latest_price"] else 0.00,
                "pnl": read_from_db(pos["unrealized_pnl"]) if pos["unrealized_pnl"] else 0.00,
            })

    # Return a pandas DataFrame for easy integration with Streamlit
    df = pd.DataFrame(results)

    # Optional: sort and format
    if not df.empty:
        df = df.sort_values(by=["instrument", "type", "date"], ascending=[True, True, True])
        df.reset_index(drop=True, inplace=True)

    return df


def compute_closed_positions(session, account=None):
    """Compute FIFO-based realized PnL for all instruments (closed positions)."""
    results = []

    for inst_id in _get_instruments_with_trades(session, account):
        trades = _get_trades_for_instrument(session, inst_id, account)
        closed_trades, _ = _apply_fifo(trades)
        results.extend(closed_trades)

    return results


def compute_open_positions(session, account=None):
    """Compute open positions (unrealized PnL) using FIFO."""
    results = []

    for inst_id in _get_instruments_with_trades(session, account):
        trades = _get_trades_for_instrument(session, inst_id, account)
        _, open_lots = _apply_fifo(trades)

        if not open_lots:
            continue

        total_qty = sum(l["remaining_qty"] for l in open_lots)
        total_cost = sum(l["remaining_qty"] * l["price"] for l in open_lots)
        avg_cost = total_cost / total_qty if total_qty else None

        latest_price = _get_latest_market_price(session, inst_id)
        unrealized_pnl = (
            (latest_price - avg_cost) * total_qty
            if latest_price is not None and avg_cost is not None
            else None
        )

        instrument = session.get(Instrument, inst_id)

        results.append({
            "instrument": instrument,
            "instrument_id": inst_id,
            "quantity": total_qty,
            "avg_cost": avg_cost,
            "latest_price": latest_price,
            "unrealized_pnl": unrealized_pnl,
        })

    return results


# --------------------------------------------------------------------------------------------------------
# older function definitions

def get_portfolio_value(session):
    total_cents = 0
    instruments = session.query(Instrument).all()
    for inst in instruments:
        qty, _ = get_position(session, inst.id)
        if qty <= 0:
            continue
        last_price = session.query(OHLCV.close).filter_by(instrument_id=inst.id).order_by(OHLCV.timestamp.desc()).first()
        if last_price:
            total_cents += qty * last_price[0]

    global_cash = session.query(func.sum(Transaction.amount)).filter(Transaction.instrument_id.is_(None)).scalar() or 0
    total_cents += global_cash
    print(f"📊 Portfolio value (including global transactions): {read_from_db(total_cents):.2f}")
    return read_from_db(total_cents)

def get_latest_market_price(session, instrument):
    pass

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


# def load_market_prices_from_symbol(symbol: Symbol):
#     """
#     Given a DataFrame with 'timestamp' and 'close' columns,
#     inserts MarketPrice rows for the instrument identified by ticker.
#     """

#     session = get_session()
#     session.begin()

#     df = symbol.ochlv_df
#     ticker = symbol.name

#     # Lookup instrument ID
#     instrument = session.execute(
#         select(Instrument).where(Instrument.ticker == ticker)
#     ).scalar_one_or_none()

#     if instrument is None:
#         raise ValueError(f"No instrument found for ticker '{ticker}'")

#     instrument_id = instrument.id

#     # Ensure timestamps are datetime
#     df['timestamp'] = pd.to_datetime(df['timestamp'])

#     # Prepare data
#     prices = []
#     for _, row in df.iterrows():
#         date = row['timestamp']
#         price_cents = save_to_db(float(row['close']))
#         prices.append(
#             MarketPrice(
#                 instrument_id=instrument_id,
#                 date=date,
#                 price=price_cents,
#             )
#         )

#     inserted = 0
#     skipped = 0
#     for mp in prices:
#         session.add(mp)
#         try:
#             session.flush()  # catch duplicates (violates unique constraint)
#             inserted += 1
#         except IntegrityError:
#             session.rollback()
#             skipped += 1

#     session.commit()

#     print(f"Inserted {inserted} new prices, skipped {skipped} duplicates.")


def load_ohlcv_from_symbol_bulk(symbol: Symbol):
    """
    Insert the Symbol.ochlv_df into the OHLCV table.

    Args:
        session: SQLAlchemy Session
        symbol_obj: Symbol dataclass instance
        granularity: str, e.g. "1d", "1h", "1m"
    """

    if symbol.ochlv_df.empty:
        print("No OHCLV data to insert.")
        return

    # Prepare list of dicts for bulk insert
    records = []
    for _, row in symbol.ochlv_df.iterrows():
        records.append({
            "symbol": symbol.ticker,
            "timestamp": row["timestamp"],
            "granularity": symbol.data_granularity,
            "open": int(row["open"] * 1_000_000),   # optional: store as integer if needed
            "high": int(row["high"] * 1_000_000),
            "low": int(row["low"] * 1_000_000),
            "close": int(row["close"] * 1_000_000),
            "volume": int(row["volume"] or 0),
        })

    with get_session() as session, session.begin():
        try:
            session.bulk_insert_mappings(OHLCV, records)
            session.commit()
            print(f"Inserted {len(records)} rows for symbol {symbol.ticker}.")
        except Exception as e:
            session.rollback()
            print(f"Error inserting OHLCV data: {e}")


def load_ohlcv_from_symbol(symbol: Symbol, create_instrument: Boolean):
    """
    Insert OHLCV rows, skipping duplicates efficiently.
    """
    if symbol.ochlv_df.empty:
        print("No OHLCV data to insert.")
        return

    df = symbol.ochlv_df
    inserted = 0
    skipped = 0

    with get_session() as session, session.begin():

        # Get the Instrument
        instrument = session.query(Instrument).filter_by(ticker=symbol.ticker).first()
        if not instrument:
            if not create_instrument:
                raise Exception(f"No Instrument found with ticker: {symbol.ticker}")
            else:
                i = Instrument()
                i.ticker = symbol.ticker
                i.name = symbol.name
                i.name_long = symbol.long_name
                i.currency = symbol.currency
                session.add(i)
                session.flush()

        # Pre-fetch existing timestamps for this symbol
        existing_timestamps = set(
            session.scalars(
                select(OHLCV.timestamp).where(OHLCV.instrument_id == instrument.id)
            ).all()
        )

        for _, row in df.iterrows():
            ts = row["timestamp"]
            if ts in existing_timestamps:
                skipped += 1
                continue

            entry = OHLCV(
                instrument_id=instrument.id,
                timestamp=ts,
                granularity=symbol.data_granularity,
                open=int(row["open"] * 1_000_000),
                high=int(row["high"] * 1_000_000),
                low=int(row["low"] * 1_000_000),
                close=int(row["close"] * 1_000_000),
                volume=int(row["volume"] or 0),
            )

            session.add(entry)
            inserted += 1

        session.commit()

    print(f"Inserted {inserted} new OHLCV rows, skipped {skipped} existing.")

