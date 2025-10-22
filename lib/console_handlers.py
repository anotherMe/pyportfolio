
import pandas as pd
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
from lib.models import OHLCV, MarketPrice, Instrument
from lib.database import init_db, get_session, save_to_db
from lib.myYahooFinance import Symbol, YahooSymbolParser
from sqlalchemy.orm import Session


def handle_init_db():
    init_db()

def handle_load_data(args):

    parser = YahooSymbolParser(args.file)
    if parser.symbol:
        load_market_prices_from_symbol(parser.symbol)
    else:
        print("No symbol present")

def load_market_prices_from_symbol(symbol: Symbol):
    """
    Given a DataFrame with 'timestamp' and 'close' columns,
    inserts MarketPrice rows for the instrument identified by ticker.
    """

    df = symbol.ochlv_df
    ticker = symbol.name

    with get_session() as session:
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


def insert_ohlcv_from_symbol(session: Session, symbol: Symbol):
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

    try:
        session.bulk_insert_mappings(OHLCV, records)
        session.commit()
        print(f"Inserted {len(records)} rows for symbol {symbol.name}.")
    except Exception as e:
        session.rollback()
        print(f"Error inserting OHLCV data: {e}")
