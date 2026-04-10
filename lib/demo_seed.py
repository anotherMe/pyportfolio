
import random
from datetime import datetime, timedelta, timezone

from faker import Faker

from lib.database import write_to_db
from lib.enums import TradeType, TransactionType, DistributionPolicy, OHLCVGranularity
from lib.models import Account, Instrument, Trade, Transaction, OHLCV, Position

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
        session.query(Position).delete()
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
        Instrument(isin="US0378331005", ticker="AAPL", name="Apple Inc.", dist_policy=DistributionPolicy.DISTRIBUTING, currency="USD"),
        Instrument(isin="US5949181045", ticker="MSFT", name="Microsoft Corp", dist_policy=DistributionPolicy.ACCUMULATING, currency="USD"),
        Instrument(isin="LU1681046931", ticker="ETF-EM", name="Emerging Markets ETF", dist_policy=DistributionPolicy.ACCUMULATING, currency="EUR"),
    ]
    session.add_all(instruments)
    session.flush()

    # --- Positions (one per account + instrument combination) ---
    positions = []
    for acc in accounts:
        for instr in instruments:
            pos = Position(account_id=acc.id, instrument_id=instr.id, closed=False)
            positions.append(pos)
    session.add_all(positions)
    session.flush()

    # --- Trades ---
    trades = []
    for pos in positions:
        # Start with buy-only trades
        for _ in range(random.randint(2, 4)):
            trade = Trade(
                position_id=pos.id,
                date=fake.date_time_between(start_date="-1y", end_date="now").replace(tzinfo=timezone.utc),
                type=TradeType.BUY,
                quantity=random.randint(10, 200),
                price=write_to_db(random.randint(80, 300)),
                description=fake.sentence(),
            )
            trades.append(trade)

        # Then mixed buy/sell trades
        for _ in range(random.randint(2, 4)):
            trade = Trade(
                position_id=pos.id,
                date=fake.date_time_between(start_date="-1y", end_date="now").replace(tzinfo=timezone.utc),
                type=random.choice(list(TradeType)),
                quantity=random.randint(10, 200),
                price=write_to_db(random.randint(80, 300)),
                description=fake.sentence(),
            )
            trades.append(trade)

    session.add_all(trades)
    session.flush()

    # --- Transactions ---
    transactions = []
    for trade in trades:
        if random.random() < 0.4:
            transactions.append(
                Transaction(
                    account_id=trade.position.account_id,
                    position_id=trade.position_id,
                    date=(trade.date + timedelta(days=1)),
                    type=random.choice(list(TransactionType)),
                    amount=write_to_db(abs(random.randint(1, 100))),
                    description=fake.sentence(),
                )
            )
    session.add_all(transactions)

    # --- OHLCV data ---
    ohlcvs = []
    for instr in instruments:
        ts = datetime.now(tz=timezone.utc) - timedelta(days=30)
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
                    granularity=OHLCVGranularity.DAY.value,
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
