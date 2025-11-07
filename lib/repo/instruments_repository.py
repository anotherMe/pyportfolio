
from lib.models import Instrument


def add_instrument(session, isin, name, ticker=None, category=None, currency="EUR"):

    instrument = Instrument(isin=isin, name=name, ticker=ticker, category=category, currency=currency)
    try:
        session.add(instrument)
        session.commit()
        print(f"🗑️ Added instrument ID {instrument.id}")
    except Exception as e:
        session.rollback()
        print(f"⚠️ Cannot add instrument ID {instrument.id}: {e}")
        return False    
    return True

def get_instrument_by_isin(session, isin):
    return session.query(Instrument).filter_by(isin=isin).first()

def get_instrument_by_ticker(session, ticker):
    return session.query(Instrument).filter_by(ticker=ticker,).first()

def get_all_instruments(session):
    return session.query(Instrument).all()

def delete_instrument(session, instrument_id):
    instrument = session.get(Instrument, instrument_id)
    if instrument:
        try:
            # Attempt to delete the instrument
            session.delete(instrument)
            session.commit()
            print(f"🗑️ Deleted instrument ID {instrument_id}")
        except Exception as e:
            session.rollback()
            print(f"⚠️ Cannot delete instrument ID {instrument_id}: {e}")
            return False    
        return True
    else:
        print(f"⚠️ Instrument ID {instrument_id} not found.")
        return False
    