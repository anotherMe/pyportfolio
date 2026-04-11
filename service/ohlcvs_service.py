from typing import Optional

from sqlalchemy.orm import Session

import lib.repo.ohlcvs_repository as repo
from lib.database import read_from_db
from service.dtos import PriceDTO


class OhlcvsService:

    def get_latest_prices_for_instrument_list(self, session, instrument_ids: list[int]) -> list[PriceDTO]:
        results = repo.get_latest_prices_for_instrument_list(session, instrument_ids)
        return [
            PriceDTO(instrument_id=r.instrument_id, date=r.timestamp, granularity=r.granularity, open=read_from_db(r.open),
                     high=read_from_db(r.high), low=read_from_db(r.low), close=read_from_db(r.close), volume=read_from_db(r.volume))
            for r in results
        ]

    def get_latest_price(self, session, instrument_id: int) -> Optional[PriceDTO]:
        r = repo.get_latest_price(session, instrument_id)
        if r is None:
            return None
        return PriceDTO(instrument_id=r.instrument_id, date=r.date, granularity=r.granularity, 
                        open=read_from_db(r.open), high=read_from_db(r.high), low=read_from_db(r.low), 
                        close=read_from_db(r.close), volume=read_from_db(r.volume))

    def get_prices_for_instrument(self, session: Session, instrument_id: int, granularity: str = "1d") -> list[PriceDTO]:
        results = repo.get_prices_for_instrument(session, instrument_id, granularity)
        return [
            PriceDTO(instrument_id=r.instrument_id, date=r.timestamp, granularity=r.granularity, open=read_from_db(r.open),
                     high=read_from_db(r.high), low=read_from_db(r.low), close=read_from_db(r.close), volume=read_from_db(r.volume))
            for r in results
        ]

# -----------------------
# Module-level alias (backwards compatibility)
# -----------------------

_service = OhlcvsService()


def get_latest_prices_for_instrument_list(session, instrument_ids: list[int]) -> list[PriceDTO]:
    return _service.get_latest_prices_for_instrument_list(session, instrument_ids)
