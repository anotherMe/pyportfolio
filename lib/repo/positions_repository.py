
from typing import Optional
from attr import dataclass
import pandas as pd
from sqlalchemy import func, select, case
from lib.database import read_from_db
from lib.models import Position, Trade, Transaction, UTCDateTime
from lib.repo.prices_repository import get_latest_prices
from lib.repo.trades_repository import get_all_trades

from logging_config import setup_logger
from service.custom_exceptions import PortfolioException
log = setup_logger(__name__)


# -----------------------
# - DTO Models
# -----------------------

@dataclass
class PositionDTO:
    """Data Transfer Object for Position summary."""

    position_id: int
    opening_date: Optional[UTCDateTime] = None
    instrument_id: int = 0
    instrument_name: str = ""
    avg_buy_price: float = 0.00
    realized_pnl: float = 0.00
    unrealized_pnl: float = 0.00
    # pnl_percent: float = 0.00
    transactions_amount: float = 0.00
    closing_date: Optional[UTCDateTime] = None
    remaining_quantity: int = 0
    type: str = "open"  # 'open' or 'closed'  # FIXME: I don't like this field: can we infer it from remaining_quantity?


# ----------------------------
# 🔹 Utility functions
# ----------------------------

def _get_totals(session):

    total_buy_price = case(
        (Trade.type == "buy", Trade.price * Trade.quantity),
        else_=0,
    )

    total_buy_quantity = case(
        (Trade.type == "buy", Trade.quantity),
        else_=0,
    )

    remaining_qty = case(
        (Trade.type == "buy", Trade.quantity),
        else_=-Trade.quantity,
    )

    stmt = (
        select(
            Position.id.label("position_id"),
            func.sum(remaining_qty).label("remaining_quantity"),
            (
                func.sum(total_buy_price) /
                func.nullif(func.sum(total_buy_quantity), 0)
            ).label("avg_buy_price"),
            func.sum(Transaction.amount).label("transactions_amount_total"),
        )
        .join(Trade, Trade.position_id == Position.id)
        .outerjoin(Transaction, Transaction.position_id == Position.id)
        .group_by(Position.id)
    )

    return session.execute(stmt).mappings().all()


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
                
            if positionDTO.type == 'closed':
                raise PortfolioException("Trade encountered after position was closed.")
                
            if current_trade.type == "buy":

                if positionDTO.remaining_quantity == 0:  # first buy
                    positionDTO.opening_date = current_trade.date
                    positionDTO.remaining_quantity = current_trade.quantity
                    positionDTO.avg_buy_price = read_from_db(current_trade.price)

                else:
                    # update aggregate buys
                    positionDTO.remaining_quantity += current_trade.quantity
                    # update weighted average price
                    total_cost = (positionDTO.avg_buy_price * (positionDTO.remaining_quantity - current_trade.quantity)) + (current_trade.price * current_trade.quantity)
                    positionDTO.avg_buy_price = total_cost / positionDTO.remaining_quantity

            elif current_trade.type == "sell":

                if positionDTO.remaining_quantity == 0:
                    raise PortfolioException("Sell trade encountered without a preceding buy trade.")

                positionDTO.realized_pnl += ( read_from_db(current_trade.price) - positionDTO.avg_buy_price ) * current_trade.quantity

                positionDTO.remaining_quantity -= current_trade.quantity

                if positionDTO.remaining_quantity < 0:
                    raise PortfolioException("Sell quantity exceeds available bought quantity in FIFO calculation.")

                # Check if position is now closed ( ie: all quantity sold)
                if positionDTO.remaining_quantity == 0:
                    positionDTO.type = 'closed'
                    positionDTO.closing_date = current_trade.date
                    continue

        # If current position is still open, calculate unrealized PnL on remaining quantity
        if positionDTO.remaining_quantity > 0:

            if positionDTO.type != 'open':
                raise PortfolioException("Position with remaining quantity is not marked as open.")

            latest_price_entry = next((price for price in latest_prices if price['instrument_id'] == position.instrument.id), None)
            latest_price = read_from_db(latest_price_entry['price']) if latest_price_entry else 0.0

            positionDTO.unrealized_pnl = latest_price * positionDTO.remaining_quantity

        positionDTOs.append(positionDTO)

    return positionDTOs


# ----------------------------
# 🔸 Public API
# ----------------------------

def get_all_positions(session, account=None):

    stmt = select(Position)
    if account:
        stmt = stmt.filter_by(account_id=account.id)
    return session.scalars(stmt).all()


def get_positions_summary(session, account=None, include_closed=True, include_open=True):
    """
        Retrieve positions summary as a pandas DataFrame.
    """

    # all_positions = _apply_fifo(session, account)

    all_positions = get_all_positions(session, account)

    filtered_positions = []
    for pos in all_positions:

        if  pos.closed and include_closed:
            filtered_positions.append(pos)

        if not pos.closed and include_open:
            filtered_positions.append(pos)

    ## Compute PnL and other fields
    positionsDTO = _apply_fifo(session, account)

    ## Convert to pandas DataFrame ( for easy integration with Streamlit )
    df = pd.DataFrame([vars(p) for p in positionsDTO])

    # TODO: do we still need this?
    # Sort by closing date
    if not df.empty:
        # df = df.sort_values(by=["instrument_id", "type", "closing_date"], ascending=[True, True, True])
        df = df.sort_values(by=["closing_date"], ascending=[True])
        df.reset_index(drop=True, inplace=True)

    return df

