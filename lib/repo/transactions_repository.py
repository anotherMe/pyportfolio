
from datetime import datetime
from lib.models import Account, Trade, Transaction
from lib.database import write_to_db
from sqlalchemy.orm import Session


def add_transaction(session, trans_type, amount, account, trade=None, description=None):
    tr = Transaction(
        account_id = account.id,
        trade_id=trade.id if trade else None,
        date=datetime.now(),
        type=trans_type,
        amount=write_to_db(amount),
        description=description,
    )
    session.add(tr)
    session.flush()  # ensures IDs and defaults are populated
    scope = "portfolio" if trade is None else trade.description or trade.instrument.name
    print(f"💵 Added {trans_type}: {amount:.2f} ({scope})")
    return tr

def get_all_transactions(session, account=None):
    if account:
        return session.query(Transaction).filter_by(account_id=account.id).order_by(Transaction.date).all()
    else:
        return session.query(Transaction).order_by(Transaction.date).all()

def get_transactions_for_trade_list(session: Session, trade_ids: list[int], account: Account) -> list[Transaction]:
    
    trades = (
        session.query(Transaction)
        .join(Trade, Transaction.trade_id == Trade.id)
        .filter(Trade.id.in_(trade_ids))
        .filter(Transaction.account_id == account.id)
        .order_by(Transaction.date)
        .all()
    )
    return trades

def delete_transaction(session, transaction_id):
    transaction = session.get(Transaction, transaction_id)
    if transaction:
        try:
            # Attempt to delete the transaction
            session.delete(transaction)
            session.commit()
            print(f"🗑️ Deleted transaction ID {transaction_id}")
        except Exception as e:
            session.rollback()
            print(f"⚠️ Cannot delete transaction ID {transaction_id}: {e}")
            return False    
        return True
    else:
        print(f"⚠️ Transaction ID {transaction_id} not found.")
        return False