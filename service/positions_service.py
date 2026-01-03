

from typing import Optional
from attr import dataclass
import pandas as pd
from lib.database import read_from_db
from lib.models import UTCDateTime
from lib.repo.prices_repository import get_latest_prices
from lib.repo.trades_repository import get_all_trades
from lib.repo.positions_repository import get_all_positions


from logging_config import setup_logger
from service.custom_exceptions import PortfolioException
log = setup_logger(__name__)


# -----------------------
# -- DTO Models
# -----------------------

@dataclass
class PositionDTO:
    """Data Transfer Object for Position summary."""

    position_id: int
    instrument_id: int = 0
    instrument_name: str = ""
    opening_date: Optional[UTCDateTime] = None
    avg_buy_price: float = 0.00
    total_buy_cost: float = 0.00
    realized_pnl: float = 0.00
    unrealized_pnl: float = 0.00
    transactions_amount: float = 0.00
    closing_date: Optional[UTCDateTime] = None
    remaining_quantity: int = 0


# ----------------------------
# 🔹 Utility functions
# ----------------------------

def _apply_fifo(session, account):
    """
    Apply FIFO to trades of the same Instrument
    Returns:
        closed_trades: list of dicts with realized PnL
        open_lots: remaining open lots (list of dicts)
    """

    all_trades = get_all_trades(session, account)
    latest_prices = get_latest_prices(session)

    positionDTOs = []

    for position in get_all_positions(session, account):

        positionDTO = PositionDTO(position.id)
        positionDTO.instrument_id = position.instrument.id
        positionDTO.instrument_name = position.instrument.name

        # Get trades for this position
        trades = [trade for trade in all_trades if trade.position_id == position.id]

        for current_trade in trades:
                
            if positionDTO.remaining_quantity <= 0 and positionDTO.closing_date is not None:
                raise PortfolioException(__name__, "Trade encountered after position was closed.")
                
            if current_trade.type == "buy":

                if positionDTO.remaining_quantity == 0:  # first buy
                    positionDTO.opening_date = current_trade.date
                    positionDTO.avg_buy_price = read_from_db(current_trade.price)
                    
                else:
                    total_cost = (positionDTO.avg_buy_price * (positionDTO.remaining_quantity - current_trade.quantity)) + (read_from_db(current_trade.price) * current_trade.quantity)
                    positionDTO.avg_buy_price = total_cost / positionDTO.remaining_quantity
                    
                positionDTO.remaining_quantity += current_trade.quantity
                positionDTO.total_buy_cost += read_from_db(current_trade.price) * current_trade.quantity

            elif current_trade.type == "sell":

                if positionDTO.remaining_quantity == 0:
                    raise PortfolioException(__name__, "Sell trade encountered without a preceding buy trade.")

                positionDTO.realized_pnl += ( read_from_db(current_trade.price) - positionDTO.avg_buy_price ) * current_trade.quantity

                positionDTO.remaining_quantity -= current_trade.quantity

                if positionDTO.remaining_quantity < 0:
                    raise PortfolioException(__name__, "Sell quantity exceeds available bought quantity in FIFO calculation.")

                # Check if position is now closed ( ie: all quantity sold)
                if positionDTO.remaining_quantity == 0:
                    positionDTO.closing_date = current_trade.date
                    continue

        # If current position is still open, calculate unrealized PnL on remaining quantity
        if positionDTO.remaining_quantity > 0:

            if positionDTO.closing_date is not None:
                raise PortfolioException(__name__, "Position with remaining quantity has a closing date.")

            latest_price_entry = next((price for price in latest_prices if price['instrument_id'] == position.instrument.id), None)
            latest_price = read_from_db(latest_price_entry['price']) if latest_price_entry else 0.0

            positionDTO.unrealized_pnl = ( latest_price * positionDTO.remaining_quantity ) - ( positionDTO.avg_buy_price * positionDTO.remaining_quantity )

        positionDTOs.append(positionDTO)

    return positionDTOs


def get_positions_summary(session, account=None, include_closed=True, include_open=True):
    """
        Retrieve positions summary as a pandas DataFrame.
    """

    positionsDTO = _apply_fifo(session, account)

    filtered_position_DTOs = []
    for pos in positionsDTO:

        if  pos.closing_date and include_closed:
            filtered_position_DTOs.append(pos)

        if not pos.closing_date and include_open:
            filtered_position_DTOs.append(pos)

    ## Convert to pandas DataFrame ( for easy integration with Streamlit )
    df = pd.DataFrame([vars(p) for p in filtered_position_DTOs])

    df["pnl"] = df["realized_pnl"] + df["unrealized_pnl"]
    df["pnl_percent"] = df["pnl"] / df["total_buy_cost"]

    # TODO: do we still need this?
    # Sort by closing date
    if not df.empty:
        # df = df.sort_values(by=["instrument_id", "closing_date"], ascending=[True, True, True])
        df = df.sort_values(by=["closing_date"], ascending=[True])
        df.reset_index(drop=True, inplace=True)

    return df