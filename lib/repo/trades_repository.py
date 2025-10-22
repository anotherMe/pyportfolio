
from lib.database import save_to_db
from lib.models import Trade


def get_all_trades(session, account=None):
    if account:
        return session.query(Trade).filter_by(account_id=account.id).order_by(Trade.date).all()
    else:
        return session.query(Trade).order_by(Trade.date).all()

def add_trade(session, account, instrument, date, trade_type, quantity, price, description=None):
    
    trade = Trade(
        account_id=account.id,
        instrument_id=instrument.id,
        date=date,
        type=trade_type,
        quantity=int(quantity),
        price=save_to_db(price),
        description=description,
    )
    session.add(trade)
    session.flush()  # ensures IDs and defaults are populated

    print(f"📈 Recorded trade: {trade_type.upper()} {quantity}x {instrument.ticker or instrument.name} @ {price:.2f}")

    return trade

def delete_trade(session, trade_id):
    trade = session.get(Trade, trade_id)
    if trade:
        session.delete(trade)
        session.flush()
        print(f"🗑️ Deleted trade ID {trade_id}")
        return True
    else:
        print(f"❌ Trade ID {trade_id} not found.")
        return False
