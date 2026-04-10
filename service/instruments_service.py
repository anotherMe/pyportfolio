from typing import Optional

from lib.repo.instruments_repository import (
    add_instrument,
    get_all_instruments,
    get_instrument_by_isin,
    get_instrument_by_ticker,
    delete_instrument,
)
from service.dtos import InstrumentDTO, InstrumentCreateDTO


class InstrumentsService:

    def get_all(self, session) -> list[InstrumentDTO]:
        return [InstrumentDTO.model_validate(i) for i in get_all_instruments(session)]

    def get_by_isin(self, session, isin: str) -> Optional[InstrumentDTO]:
        instrument = get_instrument_by_isin(session, isin)
        return InstrumentDTO.model_validate(instrument) if instrument else None

    def get_by_ticker(self, session, ticker: str) -> Optional[InstrumentDTO]:
        instrument = get_instrument_by_ticker(session, ticker)
        return InstrumentDTO.model_validate(instrument) if instrument else None

    def create(self, session, dto: InstrumentCreateDTO) -> InstrumentDTO:
        instrument = add_instrument(
            session,
            name=dto.name,
            currency=dto.currency,
            isin=dto.isin,
            ticker=dto.ticker,
            name_long=dto.name_long,
            dist_policy=dto.dist_policy,
            description=dto.description,
        )
        session.commit()
        return InstrumentDTO.model_validate(instrument)

    def delete(self, session, instrument_id: int) -> bool:
        result = delete_instrument(session, instrument_id)
        if result:
            session.commit()
        return result
