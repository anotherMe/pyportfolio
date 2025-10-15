
from datetime import datetime
from lib.models import Transaction
from lib.database import to_cents


def add_transaction(session, trans_type, amount, trade=None, description=None):
    tr = Transaction(
        trade_id=trade.id if trade else None,
        date=datetime.now(),
        type=trans_type,
        amount=to_cents(amount),
        description=description,
    )
    session.add(tr)
    session.flush()  # ensures IDs and defaults are populated
    scope = "portfolio" if trade is None else trade.description or trade.instrument.name
    print(f"💵 Added {trans_type}: {amount:.2f} ({scope})")
    return tr