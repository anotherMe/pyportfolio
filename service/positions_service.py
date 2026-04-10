
from collections import deque
from typing import Optional

import pandas as pd

from lib.database import read_from_db
from lib.enums import TradeType, TransactionType
from lib.models import Position
from lib.repo.positions_repository import get_all_positions, add_position, delete_position
from lib.repo.trades_repository import get_trades_for_position_list
from lib.repo.transactions_repository import get_transactions_for_position_list
from logging_config import setup_logger
from service import ohlcvs_service
from service.dtos import PositionDTO, PositionBasicDTO, PositionCreateDTO

log = setup_logger(__name__)


# -----------------------
# Utility
# -----------------------

def compute_position_closed(row):
    if row["remaining_quantity"] > 0:
        return str(row["remaining_quantity"])
    elif row["remaining_quantity"] == 0 and pd.isna(row["closing_date"]):
        return "No open quantity"
    else:
        return "Closed on " + row["closing_date"].strftime("%Y-%m-%d")


def _apply_fifo(session, positions: list[Position]) -> list[PositionDTO]:
    """Apply FIFO cost-basis matching across buy/sell trades for each position."""

    all_trades = get_trades_for_position_list(session, [p.id for p in positions])
    all_transactions = get_transactions_for_position_list(session, [p.id for p in positions])
    latest_prices = ohlcvs_service.get_latest_prices_for_instrument_list(
        session, [p.instrument.id for p in positions]
    )

    position_dtos = []
    for position in positions:

        dto = PositionDTO(position_id=position.id)
        dto.instrument_id = position.instrument.id
        dto.instrument_name = position.instrument.name
        dto.instrument_isin = position.instrument.isin
        dto.instrument_ticker = position.instrument.ticker
        dto.instrument_currency = position.instrument.currency.name
        dto.instrument_symbol = position.instrument.currency.symbol

        latest_price_entry = next(
            (p for p in latest_prices if p.instrument_id == position.instrument.id), None
        )
        dto.latest_price = latest_price_entry.price if latest_price_entry else 0.0
        dto.latest_price_date = latest_price_entry.date if latest_price_entry else None

        trades = [t for t in all_trades if t.position_id == position.id]

        for transaction in all_transactions:
            if transaction.position_id == position.id:
                if transaction.type == TransactionType.DIVIDEND:
                    dto.transactions_amount += read_from_db(transaction.amount)
                else:
                    dto.transactions_amount -= read_from_db(transaction.amount)

        fifo_queue: deque = deque()
        for trade in trades:
            qty = trade.quantity
            price = read_from_db(trade.price)

            if trade.type == TradeType.BUY:
                fifo_queue.append({"qty": qty, "cost_per_unit": price})
                dto.total_invested += qty * price
                if len(fifo_queue) == 1:
                    dto.opening_date = trade.date

            else:  # SELL
                sell_qty = qty
                sell_price = price
                while sell_qty > 0 and fifo_queue:
                    oldest_lot = fifo_queue[0]
                    matched_qty = min(oldest_lot["qty"], sell_qty)
                    dto.realized_pnl += matched_qty * (sell_price - oldest_lot["cost_per_unit"])
                    oldest_lot["qty"] -= matched_qty
                    sell_qty -= matched_qty
                    if oldest_lot["qty"] == 0:
                        fifo_queue.popleft()
                        dto.closing_date = trade.date

        for lot in fifo_queue:
            dto.remaining_quantity += lot["qty"]
            dto.remaining_cost_basis += lot["qty"] * lot["cost_per_unit"]

        current_value = dto.remaining_quantity * dto.latest_price
        dto.unrealized_pnl = current_value - dto.remaining_cost_basis
        dto.realized_pnl_percent = (dto.realized_pnl / dto.total_invested * 100) if dto.total_invested > 0 else 0.0
        dto.unrealized_pnl_percent = (dto.unrealized_pnl / dto.remaining_cost_basis * 100) if dto.remaining_cost_basis > 0 else 0.0

        position_dtos.append(dto)

    return position_dtos


# -----------------------
# Service
# -----------------------

class PositionsService:

    def get_summary(self, session, account=None, account_id: int = None, include_closed: bool = True, include_open: bool = True) -> pd.DataFrame:
        """Return a pandas DataFrame with FIFO-computed position summaries.
        Accepts either an Account ORM object (legacy) or an account_id int.
        """
        all_positions = get_all_positions(session, account, account_id=account_id)
        dtos = _apply_fifo(session, all_positions)

        filtered = [
            p for p in dtos
            if (p.closing_date and include_closed) or (not p.closing_date and include_open)
        ]

        df = pd.DataFrame([p.model_dump() for p in filtered])

        if not df.empty:
            df["position_closed"] = df.apply(compute_position_closed, axis=1)
            df["pnl"] = df["realized_pnl"] + df["unrealized_pnl"] + df["transactions_amount"]
            df["pnl_percent"] = df["pnl"] / df["total_invested"]
            df = df.sort_values(by=["opening_date"], ascending=[True])
            df.reset_index(drop=True, inplace=True)

        return df

    def get_position_summary(self, session, position_id: int) -> PositionDTO:
        """Return a single PositionDTO with computed P&L."""
        position = session.get(Position, position_id)
        if position is None:
            raise ValueError(f"Position {position_id} not found")
        dtos = _apply_fifo(session, [position])
        p = dtos[0]
        p.pnl = p.realized_pnl + p.unrealized_pnl + p.transactions_amount
        p.pnl_percent = (p.pnl / p.total_invested) if p.total_invested > 0 else 0.0
        return p

    def get_all_basic(self, session, account=None, account_id: int = None) -> list[PositionBasicDTO]:
        """Return lightweight position info — no FIFO, suitable for dropdowns."""
        positions = get_all_positions(session, account, account_id=account_id)
        result = []
        for pos in positions:
            result.append(PositionBasicDTO(
                id=pos.id,
                account_id=pos.account_id,
                account_name=pos.account.name,
                instrument_id=pos.instrument.id,
                instrument_name=pos.instrument.name,
                instrument_ticker=pos.instrument.ticker or "",
                instrument_currency=pos.instrument.currency.name,
                instrument_symbol=pos.instrument.currency.symbol,
            ))
        return result

    def create(self, session, dto: PositionCreateDTO) -> PositionBasicDTO:
        position = add_position(session, dto.account_id, dto.instrument_id)
        session.commit()
        return PositionBasicDTO(
            id=position.id,
            account_id=position.account_id,
            account_name=position.account.name,
            instrument_id=position.instrument.id,
            instrument_name=position.instrument.name,
            instrument_ticker=position.instrument.ticker or "",
            instrument_currency=position.instrument.currency.name,
            instrument_symbol=position.instrument.currency.symbol,
        )

    def delete(self, session, position_id: int) -> bool:
        result = delete_position(session, position_id)
        if result:
            session.commit()
        return result


# -----------------------
# Module-level aliases (backwards compatibility for existing callers)
# -----------------------

_service = PositionsService()


def get_positions_summary(session, account=None, include_closed=True, include_open=True) -> pd.DataFrame:
    return _service.get_summary(session, account, include_closed, include_open)


def get_position_summary(session, position) -> PositionDTO:
    """Backward-compatible alias. Accepts a Position model instance or position_id int."""
    position_id = position if isinstance(position, int) else position.id
    return _service.get_position_summary(session, position_id)
