
from sqlalchemy import select
from lib.models import Position
from logging_config import setup_logger
log = setup_logger(__name__)


def get_all_positions(session, account=None):

    stmt = select(Position)
    if account:
        stmt = stmt.filter_by(account_id=account.id)
    return session.scalars(stmt).all()

