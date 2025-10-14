
from sqlalchemy import create_engine, func, case, desc
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
    session.flush()  # ensures IDs and defaults are populated
    print(f"➕ Added instrument: {name} ({isin})")
    return instrument

def get_instrument_by_isin(session, isin):
    return session.query(Instrument).filter_by(isin=isin).first()

def get_all_instruments(session):
    return session.query(Instrument).all()


# ----------------------------------------------------------
# Trades
# ----------------------------------------------------------
def add_trade(session, instrument, trade_type, quantity, price, fees, tax_rate, description=None):
    
    trade = Trade(
        instrument_id=instrument.id,
        date=datetime.now(),
        type=trade_type,
        quantity=int(quantity),
        price=to_cents(price),
        description=description,
    )
    session.add(trade)
    session.flush()  # ensures IDs and defaults are populated

    print(f"📈 Recorded trade: {trade_type.upper()} {quantity}x {instrument.ticker or instrument.name} @ {price:.2f}")

    return trade

def get_current_quantity(session, instrument_id):
    buys = (
        session.query(Trade)
        .filter(Trade.instrument_id == instrument_id, Trade.type == "buy")
        .with_entities(func.sum(Trade.quantity))
        .scalar() or 0.0
    )
    sells = (
        session.query(Trade)
        .filter(Trade.instrument_id == instrument_id, Trade.type == "sell")
        .with_entities(func.sum(Trade.quantity))
        .scalar() or 0.0
    )
    return buys - sells

def get_position(session, instrument_id):
    net_qty = get_current_quantity(session, instrument_id)
    if net_qty <= 0:
        return 0, 0.0

    avg_price_cents = get_average_buy_price(session, instrument_id)
    return net_qty, avg_price_cents

def get_average_buy_price(session, instrument_id):
    """
    Compute FIFO-based average buy price for the currently owned quantity of an instrument.
    """

    # Retrieve trades in chronological order
    trades = (
        session.query(Trade)
        .filter(Trade.instrument_id == instrument_id)
        .order_by(Trade.date)
        .all()
    )

    inventory = []  # list of [qty_remaining, price_per_unit]
    for trade in trades:
        if trade.type == "buy":
            inventory.append([trade.quantity, trade.price])
        elif trade.type == "sell":
            qty_to_sell = trade.quantity
            while qty_to_sell > 0 and inventory:
                first_lot = inventory[0]
                if first_lot[0] <= qty_to_sell:
                    qty_to_sell -= first_lot[0]
                    inventory.pop(0)
                else:
                    first_lot[0] -= qty_to_sell
                    qty_to_sell = 0

    total_qty = sum(q for q, _ in inventory)
    total_cost = from_cents(sum(q * p for q, p in inventory))
    return total_cost / total_qty if total_qty > 0 else 0.0

# ----------------------------------------------------------
# Market Prices
# ----------------------------------------------------------

def add_market_price(session, instrument, price):
    mp = MarketPrice(instrument_id=instrument.id, date=datetime.now(), price=to_cents(price))
    session.add(mp)
    session.flush() # ensures IDs and defaults are populated
    print(f"💰 Added market price for {instrument.name}: {price:.2f}")
    return mp

def get_latest_market_price(session, instrument_id):
    last_price_row = (
        session.query(MarketPrice)
        .filter(MarketPrice.instrument_id == instrument_id)
        .order_by(desc(MarketPrice.date))
        .first()
    )
    return from_cents(last_price_row.price) if last_price_row else None

# ----------------------------------------------------------
# Transactions
# ----------------------------------------------------------
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
