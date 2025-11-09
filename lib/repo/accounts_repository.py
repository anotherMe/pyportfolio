
from lib.models import Account


def add_account(session, name, description):

    account = Account(
        name=name,
        description=description
    )
    try:
        session.add(account)
        session.commit()
        print(f"🗑️ Added account ID {account.id}")
    except Exception as e:
        session.rollback()
        print(f"⚠️ Cannot add account ID {account.id}: {e}")
        return False    
    return True

def get_all_accounts(_session):
    return _session.query(Account).all()

def get_account_by_name(session, account_name):
    return session.query(Account).filter_by(name=account_name).first()

def delete_account(session, account_id):
    account = session.get(Account, account_id)
    if account:
        try:
            # Attempt to delete the account
            session.delete(account)
            session.commit()
            print(f"🗑️ Deleted account ID {account_id}")
        except Exception as e:
            session.rollback()
            print(f"⚠️ Cannot delete account ID {account_id}: {e}")
            return False    
        return True
    else:
        print(f"⚠️ Account ID {account_id} not found.")
        return False
    