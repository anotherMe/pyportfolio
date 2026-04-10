
from lib.database import write_to_db
from lib.models import Trade, Position
from lib.enums import TradeType
from sqlalchemy.orm import Session


def get_all_trades(session) -> list[Trade]:
    return session.query(Trade).order_by(Trade.date).all()


def get_all_trades_by_account(session, account) -> list[Trade]:
    return (
        session.query(Trade)
        .join(Position, Trade.position_id == Position.id)
        .filter(Position.account_id == account.id)
        .order_by(Trade.date)
        .all()
    )


def get_trades_for_position_list(session: Session, position_ids: list[int]) -> list[Trade]:
    return (
        session.query(Trade)
        .filter(Trade.position_id.in_(position_ids))
        .order_by(Trade.date)
        .all()
    )


def add_trade(session, position_id: int, date, trade_type: TradeType, quantity: int, price: float, description: str = None) -> Trade:
    trade = Trade(
        position_id=position_id,
        date=date,
        type=trade_type,
        quantity=int(quantity),
        price=write_to_db(price),
        description=description,
    )
    session.add(trade)
    session.flush()
    return trade


def delete_trade(session, trade_id: int) -> bool:
    trade = session.get(Trade, trade_id)
    if trade:
        session.delete(trade)
        session.flush()
        return True
    return False
