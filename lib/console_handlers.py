
import pandas as pd
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
from lib.models import MarketPrice, Instrument
from lib.database import init_db, get_session, save_to_db
from lib.myYahooFinance import Symbol


def handle_init_db():
    init_db()

def handle_load_data(args):
    symbol = Symbol(args.file)
    symbol.load()
    load_market_prices_from_df(symbol.ochlvDf, symbol.name)



def load_market_prices_from_df(df: pd.DataFrame, ticker: str):
    """
    Given a DataFrame with 'timestamp' and 'close' columns,
    inserts MarketPrice rows for the instrument identified by ticker.
    """

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
