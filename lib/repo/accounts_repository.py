
from lib.models import Account


def add_account(session, name: str, description: str = None) -> Account:
    account = Account(name=name, description=description)
    session.add(account)
    session.flush()
    return account


def get_all_accounts(session) -> list[Account]:
    return session.query(Account).all()


def get_account_by_name(session, account_name: str) -> Account | None:
    return session.query(Account).filter_by(name=account_name).first()


def delete_account(session, account_id: int) -> bool:
    account = session.get(Account, account_id)
    if account:
        session.delete(account)
        session.flush()
        return True
    return False
