
from lib.models import Instrument
from lib.enums import Currency, DistributionPolicy


def add_instrument(session, name: str, currency: Currency, isin: str = None, ticker: str = None, name_long: str = None, dist_policy: DistributionPolicy = None, description: str = None) -> Instrument:
    instrument = Instrument(
        isin=isin,
        ticker=ticker,
        name=name,
        name_long=name_long,
        dist_policy=dist_policy,
        currency=currency,
        description=description,
    )
    session.add(instrument)
    session.flush()
    return instrument


def get_instrument_by_isin(session, isin: str) -> Instrument | None:
    return session.query(Instrument).filter_by(isin=isin).first()


def get_instrument_by_ticker(session, ticker: str) -> Instrument | None:
    return session.query(Instrument).filter_by(ticker=ticker).first()


def get_all_instruments(session) -> list[Instrument]:
    return session.query(Instrument).all()


def delete_instrument(session, instrument_id: int) -> bool:
    instrument = session.get(Instrument, instrument_id)
    if instrument:
        session.delete(instrument)
        session.flush()
        return True
    return False
