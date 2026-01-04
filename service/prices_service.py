
import lib.repo.prices_repository as repo
from lib.database import read_from_db


class PriceDTO:
    def __init__(self, instrument_id: int, price: float, date):
        self.instrument_id = instrument_id
        self.price = price
        self.date = date

def get_latest_prices_for_instrument_list(session, inst_ids: list[int]) -> list[PriceDTO]:

    results = repo.get_latest_prices_for_instrument_list(session, inst_ids)
    price_dtos = []
    for instrument_id, price, date in results:
        price_dtos.append(PriceDTO(instrument_id, read_from_db(price), date))
    return price_dtos