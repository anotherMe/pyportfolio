
from sqlalchemy import desc, select, func, outerjoin
from sqlalchemy.orm import aliased
from lib.database import write_to_db, read_from_db
from lib.models import OHLCV, Instrument


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

def get_latest_closing_price_OLD(session, instrument_id):
    
    last_price_row = (
        session.query(OHLCV)
        .filter(OHLCV.instrument_id == instrument_id)
        .order_by(desc(OHLCV.timestamp))
        .first()
    )
    
    return read_from_db(last_price_row.close) if last_price_row else None

def get_latest_closing_prices(session):
        
    # Subquery: get latest timestamp for each instrument
    latest_ts_subq = (
        select(
            OHLCV.instrument_id,
            func.max(OHLCV.timestamp).label("latest_ts")
        )
        .group_by(OHLCV.instrument_id)
        .subquery()
    )

    # Alias OHLCV for joining
    ohlcv_latest = aliased(OHLCV)

    # Main query: left join instruments with latest ohlcv data
    query = (
        select(
            Instrument.name.label("Instrument"),
            ohlcv_latest.close.label("Last Close"),
            ohlcv_latest.timestamp.label("Timestamp")
        )
        .outerjoin(
            latest_ts_subq,
            Instrument.id == latest_ts_subq.c.instrument_id
        )
        .outerjoin(
            ohlcv_latest,
            (ohlcv_latest.instrument_id == latest_ts_subq.c.instrument_id)
            & (ohlcv_latest.timestamp == latest_ts_subq.c.latest_ts)
        )
        .order_by(Instrument.name)
    )

    return session.execute(query).fetchall()