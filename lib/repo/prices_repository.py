
from pandas import DataFrame
from sqlalchemy import func, select
from sqlalchemy.orm import aliased
from lib.database import get_session, write_to_db
from lib.models import Price, Instrument
from service.myYahooFinanceService import YahooSymbol

from logging_config import setup_logger
log = setup_logger(__name__)

DEFAULT_TIMEZONE = "Europe/Rome"


def load_prices_from_symbol(symbol: YahooSymbol, granularity: str, instrument: Instrument):
    """
    Given a DataFrame with 'timestamp' and 'close' columns,
    inserts MarketPrice rows for the instrument identified by ticker.
    """

    dataframe = symbol.ochlv_df
    if dataframe.empty:
        print("No OHLCV data to insert.")
        return
    
    inserted = 0
    skipped = 0

    with get_session() as session, session.begin():

        # Pre-fetch existing timestamps for this symbol
        existing_timestamps = set(
            session.scalars(
                select(Price.date).where(Price.instrument_id == instrument.id)
            ).all()
        )

        for _, row in dataframe.iterrows():
            ts = row["Date"]
            if ts in existing_timestamps:
                skipped += 1
                continue

            entry = Price(
                instrument_id=instrument.id,
                date=ts,
                price=write_to_db(int(row["Close"])),
                granularity=granularity
            )

            session.add(entry)
            inserted += 1

        session.commit()

    print(f"Inserted {inserted} new prices, skipped {skipped} duplicates.")

def load_prices_from_yfinance_dataframe(dataframe: DataFrame, granularity: str, instrument: Instrument):
    """
    Given a DataFrame with 'timestamp' and 'close' columns,
    inserts MarketPrice rows for the instrument identified by ticker.
    """

    if dataframe.empty:
        print("No OHLCV data to insert.")
        return
    
    inserted = 0
    skipped = 0

    with get_session() as session, session.begin():

        # Pre-fetch existing timestamps for this symbol
        existing_timestamps = set(
            session.scalars(
                select(Price.date).where(Price.instrument_id == instrument.id)
            ).all()
        )

        for ts, row in dataframe.iterrows():
            if ts.to_pydatetime() in existing_timestamps:
                skipped += 1
                continue

            entry = Price(
                instrument_id=instrument.id,
                date=ts,
                price=write_to_db(int(row["Close"])),
                granularity=granularity
            )

            session.add(entry)
            inserted += 1

        session.commit()

    print(f"Inserted {inserted} new prices, skipped {skipped} duplicates.")

def get_latest_price(session, inst_id):
    """Return the latest market price for an instrument, or None."""
    
    stmt = (
        select(Price.price)
        .where(Price.instrument_id == inst_id)
        .order_by(Price.date.desc())
        .limit(1)
    )
    return session.scalar(stmt)

def get_latest_prices(session):
        
    # Subquery: get latest timestamp for each instrument
    latest_ts_subq = (
        select(
            Price.instrument_id,
            func.max(Price.date).label("latest_ts")
        )
        .group_by(Price.instrument_id)
        .subquery()
    )

    # Alias OHLCV for joining
    price_latest = aliased(Price)

    # Main query: left join instruments with latest ohlcv data
    query = (
        select(
            Instrument.name.label("instrument_name"),
            Instrument.ticker.label("instrument_ticker"),
            price_latest.price.label("last_close"),
            price_latest.date.label("timestamp")
        )
        .outerjoin(
            latest_ts_subq,
            Instrument.id == latest_ts_subq.c.instrument_id
        )
        .outerjoin(
            price_latest,
            (price_latest.instrument_id == latest_ts_subq.c.instrument_id)
            & (price_latest.date == latest_ts_subq.c.latest_ts)
        )
        .order_by(Instrument.name)
    )

    return session.execute(query).fetchall()