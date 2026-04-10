from typing import Optional

import lib.repo.ohlcvs_repository as repo
from lib.database import read_from_db
from service.dtos import PriceDTO


class OhlcvsService:

    def get_latest_prices_for_instrument_list(self, session, instrument_ids: list[int]) -> list[PriceDTO]:
        results = repo.get_latest_prices_for_instrument_list(session, instrument_ids)
        return [
            PriceDTO(instrument_id=instrument_id, price=read_from_db(close), date=timestamp)
            for instrument_id, close, timestamp in results
        ]

    def get_latest_price(self, session, instrument_id: int) -> Optional[PriceDTO]:
        result = repo.get_latest_price(session, instrument_id)
        if result is None:
            return None
        return PriceDTO(instrument_id=instrument_id, price=read_from_db(result.close), date=result.timestamp)


# -----------------------
# Module-level alias (backwards compatibility)
# -----------------------

_service = OhlcvsService()


def get_latest_prices_for_instrument_list(session, instrument_ids: list[int]) -> list[PriceDTO]:
    return _service.get_latest_prices_for_instrument_list(session, instrument_ids)
