import streamlit as st
import pandas as pd
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from lib.models import MarketPrice, Instrument
from lib.database import get_session


st.title("Upload Market Prices CSV (Ticker → Instrument ID)")

# Upload CSV
uploaded_file = st.file_uploader("Choose a CSV file", type="csv")

if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file)
        st.write("CSV preview:", df.head())

        # Check required columns
        required_columns = {"ticker", "date", "price"}
        if not required_columns.issubset(df.columns):
            st.error(f"CSV must contain columns: {required_columns}")
        else:
            if st.button("Insert into database"):
                inserted = 0
                skipped = 0

                with get_session() as session:
                    # Load all instruments in memory for quick lookup
                    instruments = session.execute(
                        session.query(Instrument.id, Instrument.ticker)
                    ).all()
                    ticker_to_id = {t: i for i, t in instruments}

                    for _, row in df.iterrows():
                        ticker = row['ticker']
                        instrument_id = ticker_to_id.get(ticker)

                        if instrument_id is None:
                            st.warning(f"Skipping unknown ticker: {ticker}")
                            skipped += 1
                            continue

                        try:
                            # Convert date if needed
                            if not isinstance(row['date'], datetime):
                                row_date = pd.to_datetime(row['date'])
                            else:
                                row_date = row['date']

                            # Convert price to integer cents
                            price_cents = int(float(row['price']) * 100)

                            market_price = MarketPrice(
                                instrument_id=instrument_id,
                                date=row_date,
                                price=price_cents
                            )
                            session.add(market_price)
                            session.flush()  # catch duplicates early
                            inserted += 1
                        except (IntegrityError, ValueError) as e:
                            session.rollback()
                            st.warning(f"Skipping row due to error: {e}")
                            skipped += 1

                    session.commit()
                st.success(f"Inserted {inserted} rows, skipped {skipped} rows.")
    except Exception as e:
        st.error(f"Failed to read CSV: {e}")
