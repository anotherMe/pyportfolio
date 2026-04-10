
from sqlalchemy import select
from lib.models import Position, Account, Instrument


def add_position(session, account_id: int, instrument_id: int) -> Position:
    position = Position(
        account_id=account_id,
        instrument_id=instrument_id,
        closed=False,
    )
    session.add(position)
    session.flush()
    return position


def get_all_positions(session, account=None, account_id: int = None) -> list[Position]:
    """Accepts either an Account ORM object (legacy) or an account_id int."""
    stmt = select(Position)
    resolved_id = account_id or (account.id if account else None)
    if resolved_id:
        stmt = stmt.filter_by(account_id=resolved_id)
    return session.scalars(stmt).all()


def delete_position(session, position_id: int) -> bool:
    position = session.get(Position, position_id)
    if position:
        session.delete(position)
        session.flush()
        return True
    return False
