
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from lib.models import Position, Transaction
from lib.database import write_to_db
from lib.enums import TransactionType


def add_transaction(session, account_id: int, position_id: int | None, trans_type: TransactionType, amount: float, date: datetime = None, description: str = None) -> Transaction:
    tr = Transaction(
        account_id=account_id,
        position_id=position_id,
        date=date or datetime.now(tz=timezone.utc),
        type=trans_type,
        amount=write_to_db(amount),
        description=description,
    )
    session.add(tr)
    session.flush()
    return tr


def get_all_transactions(session, account=None) -> list[Transaction]:
    if account:
        return session.query(Transaction).filter_by(account_id=account.id).order_by(Transaction.date.desc()).all()
    return session.query(Transaction).order_by(Transaction.date.desc()).all()


def get_transactions_for_position_list(session: Session, position_ids: list[int]) -> list[Transaction]:
    return (
        session.query(Transaction)
        .filter(Transaction.position_id.in_(position_ids))
        .all()
    )


def delete_transaction(session, transaction_id: int) -> bool:
    transaction = session.get(Transaction, transaction_id)
    if transaction:
        try:
            session.delete(transaction)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            print(f"⚠️ Cannot delete transaction ID {transaction_id}: {e}")
            return False
    return False
