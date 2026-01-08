
from lib.database import write_to_db
from lib.models import Trade
from sqlalchemy.orm import Session
from lib.models import Position


def get_all_trades(session):
    return session.query(Trade).order_by(Trade.date).all()
    
def get_all_trades_by_account(session, account):
    return session.query(Trade).filter_by(account_id=account.id).order_by(Trade.date).all()

def get_trades_for_position_list(session: Session, position_ids: list[int]) -> list[Trade]:
    
    trades = (
        session.query(Trade)
        .join(Position, Trade.position_id == Position.id)
        .filter(Position.id.in_(position_ids))
        .order_by(Trade.date)
        .all()
    )
    return trades

def add_trade(session, account, instrument, date, trade_type, quantity, price, description=None):
    
    trade = Trade(
        account_id=account.id,
        instrument_id=instrument.id,
        date=date,
        type=trade_type,
        quantity=int(quantity),
        price=write_to_db(price),
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
