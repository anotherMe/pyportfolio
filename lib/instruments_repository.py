
from lib.models import Instrument

def add_instrument(session, isin, name, ticker=None, category=None, currency="EUR"):
    instrument = Instrument(isin=isin, name=name, ticker=ticker, category=category, currency=currency)
    session.add(instrument)
    session.flush()  # ensures IDs and defaults are populated
    print(f"➕ Added instrument: {name} ({isin})")
    return instrument

def get_instrument_by_isin(session, isin):
    return session.query(Instrument).filter_by(isin=isin).first()

def get_all_instruments(session):
    return session.query(Instrument).all()