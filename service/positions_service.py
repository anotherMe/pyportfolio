
from collections import deque
from typing import Optional
from attr import dataclass
import pandas as pd
from lib.database import read_from_db
from lib.models import Account, Instrument, UTCDateTime
from lib.repo import accounts_repository, instruments_repository, trades_repository, transactions_repository 
from logging_config import setup_logger
from service import prices_service
from sqlalchemy.orm import Session

log = setup_logger(__name__)


# -----------------------
# -- DTO Models
# -----------------------

@dataclass
class PositionDTO:
    """Data Transfer Object for Position summary."""

    account_id: int
    instrument_id: int

    account_name: str = ""

    instrument_name: str = ""
    instrument_isin: str = ""
    instrument_ticker: str = ""

    opening_date: Optional[UTCDateTime] = None

    total_invested: float = 0.00
    
    latest_price: float = 0.00
    latest_price_date: Optional[UTCDateTime] = None
    
    transactions_amount: float = 0.00
    closing_date: Optional[UTCDateTime] = None
    remaining_quantity: int = 0
    remaining_cost_basis: float = 0.00

    realized_pnl: float = 0.00
    unrealized_pnl: float = 0.00
    realized_pnl_percent: float = 0.00
    unrealized_pnl_percent: float = 0.00


# ----------------------------
# 🔹 Utility functions
# ----------------------------

def _apply_fifo(session, instruments: list[Instrument], account: Account = None) -> list[PositionDTO]:
    """
    Apply FIFO to trades of the same Instrument
    Returns:
        closed_trades: list of dicts with realized PnL
        open_lots: remaining open lots (list of dicts)
    """

    if account:
        accounts = [account]
    else:
        accounts = accounts_repository.get_all_accounts(session)

    latest_prices = prices_service.get_latest_prices_for_instrument_list(session, [i.id for i in instruments])

    positionDTOs = []
    for account in accounts:

        all_trades = trades_repository.get_trades_for_instrument_list(session, [i.id for i in instruments], account)
        if not all_trades:  # Skip if no trades
            continue
        all_transactions = transactions_repository.get_transactions_for_trade_list(session, [i.id for i in instruments], account)

        # --- Process each instrument with trades on the current account ---
        for instrument in [i for i in instruments if any(t.instrument_id == i.id and t.account_id == account.id for t in all_trades)]:

            positionDTO = PositionDTO(account.id, instrument.id)
            positionDTO.account_name = account.name
            positionDTO.instrument_name = instrument.name
            positionDTO.instrument_isin = instrument.isin
            positionDTO.instrument_ticker = instrument.ticker

            # --- Get latest price for this instrument --- 

            latest_priceDTO_entry = next((priceDTO for priceDTO in latest_prices if priceDTO.instrument_id == instrument.id), None)
            positionDTO.latest_price = latest_priceDTO_entry.price if latest_priceDTO_entry else 0.0
            positionDTO.latest_price_date = latest_priceDTO_entry.date if latest_priceDTO_entry else None


            # --- Get Trades for this position ---

            trades = [trade for trade in all_trades if (trade.instrument_id == instrument.id and trade.account_id == account.id)]


            # --- Compute transactions amount --- 

            for transaction in all_transactions:
                if transaction.account_id == account.id:
                    if transaction.type in ('div'):
                        positionDTO.transactions_amount += read_from_db(transaction.amount)
                    else:
                        positionDTO.transactions_amount -= read_from_db(transaction.amount)


            # --- Apply FIFO logic --- 

            fifo_queue: deque = deque()
            for current_trade in trades:

                qty = current_trade.quantity
                price = read_from_db(current_trade.price)

                if current_trade.type == "buy":
                    
                    fifo_queue.append({"qty": qty, "cost_per_unit": price})
                    positionDTO.total_invested += qty * price

                    if len(fifo_queue) == 1:  # First Buy trade sets the opening date
                        positionDTO.opening_date = current_trade.date

                else:  # Sell trade

                    sell_qty = qty
                    sell_price = price

                    while sell_qty > 0 and fifo_queue:

                        oldest_lot = fifo_queue[0]
                        matched_qty = min(oldest_lot["qty"], sell_qty)

                        # Realized PnL from this matched chunk
                        positionDTO.realized_pnl += matched_qty * (sell_price - oldest_lot["cost_per_unit"])

                        # Reduce quantities
                        oldest_lot["qty"] -= matched_qty
                        sell_qty -= matched_qty

                        # Remove lot if fully consumed
                        if oldest_lot["qty"] == 0:
                            fifo_queue.popleft()
                            positionDTO.closing_date = current_trade.date  # update closing date only when a lot is fully sold


            # --- Compute remaining quantity and cost basis ---

            for lot in fifo_queue:
                positionDTO.remaining_quantity += lot["qty"]
                positionDTO.remaining_cost_basis += lot["qty"] * lot["cost_per_unit"]


            # --- PnL Calculations ---

            current_value = positionDTO.remaining_quantity * positionDTO.latest_price
            positionDTO.unrealized_pnl = current_value - positionDTO.remaining_cost_basis

            positionDTO.realized_pnl_percent = (positionDTO.realized_pnl / positionDTO.total_invested * 100) if positionDTO.total_invested > 0 else 0.0
            positionDTO.unrealized_pnl_percent = (positionDTO.unrealized_pnl / positionDTO.remaining_cost_basis * 100) if positionDTO.remaining_cost_basis > 0 else 0.0


            positionDTOs.append(positionDTO)

    return positionDTOs


def get_positions_summary(session, include_closed=True, include_open=True, account: Account = None) -> pd.DataFrame:
    """
        Retrieve positions summary as a pandas DataFrame.
    """

    all_instruments = instruments_repository.get_all_instruments(session)
    positionsDTO = _apply_fifo(session, all_instruments, account)

    filtered_position_DTOs = []
    for pos in positionsDTO:

        if  pos.closing_date and include_closed:
            filtered_position_DTOs.append(pos)

        if not pos.closing_date and include_open:
            filtered_position_DTOs.append(pos)

    ## Convert to pandas DataFrame ( for easy integration with Streamlit )
    df = pd.DataFrame([vars(p) for p in filtered_position_DTOs])

    if not df.empty:
        df["position_closed"] = df["remaining_quantity"].apply(lambda x: str(x) if x > 0 else "Position closed")
        df["pnl"] = df["realized_pnl"] + df["unrealized_pnl"] + df["transactions_amount"]
        df["pnl_percent"] = df["pnl"] / df["total_invested"]
        # TODO: do we still need sorting here ?
        # df = df.sort_values(by=["instrument_id", "closing_date"], ascending=[True, True, True])
        df = df.sort_values(by=["opening_date"], ascending=[True])
        df.reset_index(drop=True, inplace=True)

    return df


def get_position_summary(session: Session, instrument: Instrument, account: Account = None) -> PositionDTO:
    """
        Retrieve positions summary as a pandas DataFrame.
    """

    positionDTOs = _apply_fifo(session, [instrument], account)

    p = positionDTOs[0]

    # p.pnl = p.realized_pnl + p.unrealized_pnl
    p.pnl = p.realized_pnl + p.unrealized_pnl + p.transactions_amount
    p.pnl_percent = p.pnl / p.total_invested

    return p