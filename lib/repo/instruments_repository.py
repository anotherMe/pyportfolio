
from lib.models import Instrument

from logging_config import setup_logger
log = setup_logger(__name__)

def add_instrument(session, isin, name, ticker=None, category=None, currency="EUR"):

    instrument = Instrument(isin=isin, name=name, ticker=ticker, category=category, currency=currency)
    try:
        session.add(instrument)
        session.commit()
        log.info(f"🗑️ Added instrument ID {instrument.id}")
    except Exception as e:
        session.rollback()
        log.error(f"⚠️ Cannot add instrument ID {instrument.id}: {e}")
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
            log.info(f"🗑️ Deleted instrument ID {instrument_id}")
        except Exception as e:
            session.rollback()
            log.error(f"⚠️ Cannot delete instrument ID {instrument_id}: {e}")
            return False    
        return True
    else:
        log.warning(f"⚠️ Instrument ID {instrument_id} not found.")
        return False
    