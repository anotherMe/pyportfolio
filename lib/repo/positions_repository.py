
from sqlalchemy import select
from lib.models import Position


def add_position(session, account_id: int, instrument_id: int) -> Position:
    position = Position(
        account_id=account_id,
        instrument_id=instrument_id,
        closed=False,
    )
    session.add(position)
    session.flush()
    return position


def get_all_positions(session, account_id: int = 0) -> list[Position]:
    stmt = select(Position)
    if account_id != 0:
        stmt = stmt.filter_by(account_id=account_id)
    return session.scalars(stmt).all()


def delete_position(session, position_id: int) -> bool:
    position = session.get(Position, position_id)
    if position:
        session.delete(position)
        session.flush()
        return True
    return False
