from sqlalchemy import create_engine, func, case
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from lib.models import Base, Instrument, Trade, MarketPrice, Transaction

DB_PATH = "sqlite:///portfolio.db"
engine = create_engine(DB_PATH, echo=False)
SessionLocal = sessionmaker(bind=engine)

def init_db():
    Base.metadata.create_all(engine)
    print(f"✅ Database initialized at {DB_PATH}")

def get_session():
    return SessionLocal()

# ----------------------------------------------------------
# Cents conversion
# ----------------------------------------------------------
def to_cents(amount: float) -> int:
    return int(round(amount * 100))

def from_cents(cents: int) -> float:
    return cents / 100

# ----------------------------------------------------------
# Instruments
# ----------------------------------------------------------
def add_instrument(session, isin, name, ticker=None, category=None, currency="EUR"):
    instrument = Instrument(isin=isin, name=name, ticker=ticker, category=category, currency=currency)
    session.add(instrument)
    session.commit()
    print(f"➕ Added instrument: {name} ({isin})")

def get_instrument_by_isin(session, isin):
    return session.query(Instrument).filter_by(isin=isin).first()

# ----------------------------------------------------------
# Trades
# ----------------------------------------------------------
def add_trade(session, instrument, trade_type, quantity, price, fees=0.0, description=None):
    trade = Trade(
        instrument_id=instrument.id,
        date=datetime.now(),
        type=trade_type,
        quantity=int(quantity),
        price=to_cents(price),
        fees=to_cents(fees),
        description=description,
    )
    session.add(trade)
    session.commit()
    print(f"📈 Recorded trade: {trade_type.upper()} {quantity}x {instrument.ticker or instrument.name} @ {price:.2f}")

def get_position(session, instrument_id):
    """Compute net quantity and average price on the fly."""
    buy_qty = session.query(func.sum(case((Trade.type=="buy", Trade.quantity), else_=0))).filter(Trade.instrument_id==instrument_id).scalar() or 0
    sell_qty = session.query(func.sum(case((Trade.type=="sell", Trade.quantity), else_=0))).filter(Trade.instrument_id==instrument_id).scalar() or 0
    net_qty = buy_qty - sell_qty
    if net_qty <= 0:
        return 0, 0.0

    total_cost_cents = session.query(func.sum(case((Trade.type=="buy", Trade.quantity * Trade.price + Trade.fees), else_=0))).filter(Trade.instrument_id==instrument_id).scalar() or 0
    avg_price_cents = total_cost_cents // buy_qty if buy_qty else 0
    return net_qty, from_cents(avg_price_cents)

# ----------------------------------------------------------
# Market Prices
# ----------------------------------------------------------
def add_market_price(session, instrument, price):
    mp = MarketPrice(instrument_id=instrument.id, date=datetime.now(), price=to_cents(price))
    session.add(mp)
    session.commit()
    print(f"💰 Added market price for {instrument.name}: {price:.2f}")

# ----------------------------------------------------------
# Transactions
# ----------------------------------------------------------
def add_transaction(session, trans_type, amount, instrument=None, description=None):
    tr = Transaction(
        instrument_id=instrument.id if instrument else None,
        date=datetime.now(),
        type=trans_type,
        amount=to_cents(amount),
        description=description,
    )
    session.add(tr)
    session.commit()
    scope = "portfolio" if instrument is None else instrument.name
    print(f"💵 Added {trans_type}: {amount:.2f} ({scope})")

# ----------------------------------------------------------
# Portfolio value
# ----------------------------------------------------------
def get_portfolio_value(session):
    total_cents = 0
    instruments = session.query(Instrument).all()
    for inst in instruments:
        qty, _ = get_position(session, inst.id)
        if qty <= 0:
            continue
        last_price = session.query(MarketPrice.price).filter_by(instrument_id=inst.id).order_by(MarketPrice.date.desc()).first()
        if last_price:
            total_cents += qty * last_price[0]

    global_cash = session.query(func.sum(Transaction.amount)).filter(Transaction.instrument_id.is_(None)).scalar() or 0
    total_cents += global_cash
    print(f"📊 Portfolio value (including global transactions): {from_cents(total_cents):.2f}")
    return from_cents(total_cents)
