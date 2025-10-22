
import pandas as pd
from sqlalchemy import func, select
from lib.database import get_session, read_from_db
from lib.models import Instrument, MarketPrice, Trade, Transaction
from sqlalchemy.exc import IntegrityError
from lib.models import OHLCV
from lib.database import save_to_db
from lib.myYahooFinance import Symbol


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

def get_latest_market_price(session, instrument):
    pass

def get_position(session, instrument_id):
    net_qty = get_current_quantity(session, instrument_id)
    if net_qty <= 0:
        return 0, 0.0

    avg_price = get_average_buy_price(session, instrument_id)
    return net_qty, avg_price

def get_open_positions(session, account=None):

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
        "price": t.price / 1_000_000,  # convert if stored as int
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

def compute_pnl_for_sells(session):
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

def compute_fifo_pnl(session, account=None):
    """Compute FIFO-based average buy price and realized PnL for all sell trades."""

    results = []

    # --- Get a list of all Instruments involved in at least one trade ---
    if account:
            
        instruments = (
            session.execute(
                select(Trade.instrument_id)
                .where(Trade.account_id == account.id)  # filter by account
                .distinct()
            )
            .scalars()
            .all()
        )
    else:

        instruments = session.execute(select(Trade.instrument_id).distinct()).scalars().all()


    for inst_id in instruments:

        # sort trades for this instrument by date
        if account:
            trades = session.scalars(
                select(Trade)
                .where(Trade.instrument_id == inst_id, Trade.account_id == account.id)
                .order_by(Trade.date)
            ).all()
        else:
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


def load_market_prices_from_symbol(symbol: Symbol):
    """
    Given a DataFrame with 'timestamp' and 'close' columns,
    inserts MarketPrice rows for the instrument identified by ticker.
    """

    session = get_session()
    session.begin()

    df = symbol.ochlv_df
    ticker = symbol.name

    # Lookup instrument ID
    instrument = session.execute(
        select(Instrument).where(Instrument.ticker == ticker)
    ).scalar_one_or_none()

    if instrument is None:
        raise ValueError(f"No instrument found for ticker '{ticker}'")

    instrument_id = instrument.id

    # Ensure timestamps are datetime
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    # Prepare data
    prices = []
    for _, row in df.iterrows():
        date = row['timestamp']
        price_cents = save_to_db(float(row['close']))
        prices.append(
            MarketPrice(
                instrument_id=instrument_id,
                date=date,
                price=price_cents,
            )
        )

    inserted = 0
    skipped = 0
    for mp in prices:
        session.add(mp)
        try:
            session.flush()  # catch duplicates (violates unique constraint)
            inserted += 1
        except IntegrityError:
            session.rollback()
            skipped += 1

    session.commit()

    print(f"Inserted {inserted} new prices, skipped {skipped} duplicates.")


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
            "symbol": symbol.name,
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
            print(f"Inserted {len(records)} rows for symbol {symbol.name}.")
        except Exception as e:
            session.rollback()
            print(f"Error inserting OHLCV data: {e}")


def load_ohlcv_from_symbol(symbol: Symbol):
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
        
        # Pre-fetch existing timestamps for this symbol
        existing_timestamps = set(
            session.scalars(
                select(OHLCV.timestamp).where(OHLCV.symbol == symbol.name)
            ).all()
        )

        for _, row in df.iterrows():
            ts = row["timestamp"]
            if ts in existing_timestamps:
                skipped += 1
                continue

            entry = OHLCV(
                symbol=symbol.name,
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

