
from datetime import datetime, timedelta
import random
from faker import Faker
from lib.database import write_to_db
from lib.models import Account, Instrument, Trade, Transaction, OHLCV

fake = Faker()
Faker.seed(42)
random.seed(42)

def seed_demo_data(session, reset=False):
    """
    Populate the database with demo data.
    If reset=True, it deletes existing data first.
    """
    if reset:
        session.query(Transaction).delete()
        session.query(Trade).delete()
        session.query(OHLCV).delete()
        session.query(Instrument).delete()
        session.query(Account).delete()
        session.commit()

    # --- Accounts ---
    accounts = [
        Account(name="Main Portfolio", description="Primary investment account"),
        Account(name="Retirement Fund", description="Long-term savings"),
        Account(name="Demo Account", description="For presentation / testing"),
    ]
    session.add_all(accounts)
    session.flush()

    # --- Instruments ---
    instruments = [
        Instrument(isin="US0378331005", ticker="AAPL", name="Apple Inc.", category="dist", currency="USD"),
        Instrument(isin="US5949181045", ticker="MSFT", name="Microsoft Corp", category="acc", currency="USD"),
        Instrument(isin="LU1681046931", ticker="ETF-EM", name="Emerging Markets ETF", category="acc", currency="EUR"),
    ]
    session.add_all(instruments)
    session.flush()

    # --- Trades & Transactions ---
    trades = []
    for acc in accounts:
        for instr in instruments:

            # let's start with a loop of buy only trades
            for _ in range(random.randint(2, 4)):
                trade = Trade(
                    account_id=acc.id,
                    instrument_id=instr.id,
                    date=fake.date_time_between(start_date="-1y", end_date="now"),
                    type="buy",
                    quantity=random.randint(10, 200),
                    price=write_to_db(random.randint(80, 300)),
                    description=fake.sentence(),
                )
                trades.append(trade)

            # then proceed with buys and sells
            for _ in range(random.randint(2, 4)):
                trade = Trade(
                    account_id=acc.id,
                    instrument_id=instr.id,
                    date=fake.date_time_between(start_date="-1y", end_date="now"),
                    type=random.choice(["buy", "sell"]),
                    quantity=random.randint(10, 200),
                    price=write_to_db(random.randint(80, 300)),
                    description=fake.sentence(),
                )
                trades.append(trade)

    session.add_all(trades)
    session.flush()

    # Random transactions
    transactions = []
    for trade in trades:
        if random.random() < 0.4:
            transactions.append(
                Transaction(
                    account_id=trade.account_id,
                    trade_id=trade.id,
                    date=trade.date + timedelta(days=1),
                    type=random.choice(["fee", "tax", "div"]),
                    amount=write_to_db(random.randint(-50, 100)),
                    description=fake.sentence(),
                )
            )
    session.add_all(transactions)

    # --- OHLCV data ---
    ohlcvs = []
    for instr in instruments:
        ts = datetime.now() - timedelta(days=30)
        for i in range(30):
            open_p = random.randint(90, 150)
            close_p = open_p + random.randint(-5, 5)
            high_p = max(open_p, close_p) + random.randint(0, 3)
            low_p = min(open_p, close_p) - random.randint(0, 3)
            volume = random.randint(1000, 10000)
            ohlcvs.append(
                OHLCV(
                    instrument_id=instr.id,
                    timestamp=ts + timedelta(days=i),
                    granularity="1d",
                    open=write_to_db(open_p),
                    high=write_to_db(high_p),
                    low=write_to_db(low_p),
                    close=write_to_db(close_p),
                    volume=volume,
                )
            )
    session.add_all(ohlcvs)
    session.commit()

    return len(accounts), len(instruments), len(trades)
