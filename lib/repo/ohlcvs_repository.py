
from sqlalchemy import desc, select, func
from sqlalchemy.orm import aliased
from lib.database import get_session, write_to_db, read_from_db
from lib.models import OHLCV, Instrument
from lib.myYahooFinance import YahooSymbol


def add_price(session, instrument, timestamp, granularity, open, close, high=0.0, low=0.0, volume=0.0):

    ohlcv = OHLCV(
        instrument_id=instrument.id, 
        timestamp=timestamp, 
        granularity=granularity,
        open=write_to_db(open),
        high=write_to_db(high),
        low=write_to_db(low),
        close=write_to_db(close),
        volume=write_to_db(volume)
    )
    session.add(ohlcv)
    session.flush() # ensures IDs and defaults are populated
    print(f"💰 Added OHLCV for {instrument.name}")
    return ohlcv

def get_latest_price(session, inst_id):
    """Return the latest market price for an instrument, or None."""
    
    stmt = (
        select(OHLCV.close)
        .where(OHLCV.instrument_id == inst_id)
        .order_by(OHLCV.timestamp.desc())
        .limit(1)
    )
    return session.scalar(stmt)

def get_latest_prices(session):

    ohlcv_alias = aliased(OHLCV)

    subq = (
        select(
            ohlcv_alias.id,
            ohlcv_alias.instrument_id,
            ohlcv_alias.timestamp,
            func.row_number().over(
                partition_by=ohlcv_alias.instrument_id,
                order_by=ohlcv_alias.timestamp.desc()
            ).label("rnk")
        )
        .subquery()
    )

    stmt = (
        select(OHLCV)
        .join(subq, OHLCV.id == subq.c.id)
        .where(subq.c.rnk == 1)
    )

    return session.scalars(stmt).all()


def get_latest_closing_price(session, instrument_id):
    
    last_price_row = (
        session.query(OHLCV)
        .filter(OHLCV.instrument_id == instrument_id)
        .order_by(desc(OHLCV.timestamp))
        .first()
    )
    
    return read_from_db(last_price_row.close) if last_price_row else None

def load_ohlcv_from_symbol(symbol: YahooSymbol, create_instrument: bool):
    """
    Insert OHLCV rows, skipping duplicates efficiently.
    """

    df = symbol.ochlv_df
    if df.empty:
        print("No OHLCV data to insert.")
        return
    
    inserted = 0
    skipped = 0

    with get_session() as session, session.begin():

        # Get or create the Instrument
        instrument = session.query(Instrument).filter_by(ticker=symbol.ticker).first()
        if not instrument:
            if not create_instrument:
                raise Exception(f"No Instrument found with ticker: {symbol.ticker}")
            else:
                instrument = Instrument()
                instrument.ticker = symbol.ticker
                instrument.name = symbol.name
                instrument.name_long = symbol.long_name
                instrument.currency = symbol.currency
                session.add(instrument)
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
                open=write_to_db(int(row["open"])),
                high=write_to_db(int(row["high"])),
                low=write_to_db(int(row["low"])),
                close=write_to_db(int(row["close"])),
                volume=int(row["volume"] or 0),
            )

            session.add(entry)
            inserted += 1

        session.commit()

    print(f"Inserted {inserted} new OHLCV rows, skipped {skipped} existing.")

