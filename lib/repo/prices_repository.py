
from sqlalchemy import desc
from datetime import datetime
from lib.database import save_to_db, read_from_db
from lib.models import MarketPrice


def add_market_price(session, instrument, price):
    mp = MarketPrice(instrument_id=instrument.id, date=datetime.now(), price=save_to_db(price))
    session.add(mp)
    session.flush() # ensures IDs and defaults are populated
    print(f"💰 Added market price for {instrument.name}: {price:.2f}")
    return mp

def get_latest_market_price(session, instrument_id):
    last_price_row = (
        session.query(MarketPrice)
        .filter(MarketPrice.instrument_id == instrument_id)
        .order_by(desc(MarketPrice.date))
        .first()
    )
    return read_from_db(last_price_row.price) if last_price_row else None
