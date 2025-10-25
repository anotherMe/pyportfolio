
from sqlite3 import IntegrityError
import pandas as pd
from sqlalchemy import select
from lib.database import get_session, write_to_db
from lib.models import Price, Instrument
from lib.myYahooFinance import YahooSymbol

def load_prices_from_symbol(symbol: YahooSymbol, create_instrument: bool):
    """
    Given a DataFrame with 'timestamp' and 'close' columns,
    inserts MarketPrice rows for the instrument identified by ticker.
    """

    df = symbol.ochlv_df
    if df.empty:
        print("No OHLCV data to insert.")
        return
    
    inserted = 0
    skipped = 0

    with get_session() as session, session.begin():

        # Get the Instrument
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
                select(Price.date).where(Price.instrument_id == instrument.id)
            ).all()
        )

        for _, row in df.iterrows():
            ts = row["timestamp"]
            if ts in existing_timestamps:
                skipped += 1
                continue

            entry = Price(
                instrument_id=instrument.id,
                date=ts,
                price=write_to_db(int(row["close"])),
                granularity=symbol.data_granularity
            )

            session.add(entry)
            inserted += 1

        session.commit()

    print(f"Inserted {inserted} new prices, skipped {skipped} duplicates.")