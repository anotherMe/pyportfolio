from datetime import timezone

from sqlalchemy import DateTime, String, TypeDecorator

from lib.enums import Currency, TradeType, TransactionType, DistributionPolicy


class UTCDateTime(TypeDecorator):
    """
    Custom SQLAlchemy type that enforces UTC timestamps.
    Guarantees all stored and loaded datetimes are timezone-aware and in UTC.
    """
    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        """
        When writing to DB:
            - Rejects naive datetimes.
            - Converts aware datetimes to UTC.
        """
        if value is None:
            return value
        if value.tzinfo is None:
            raise ValueError("naive datetime")
        return value.astimezone(timezone.utc)

    def process_result_value(self, value, dialect):
        """
        When reading from DB:
            - Attaches UTC tzinfo to returned values.
        """
        if value is None:
            return value
        return value.replace(tzinfo=timezone.utc)


class CurrencyType(TypeDecorator):
    """
    Custom SQLAlchemy type that enforces valid Currency enum values.
    Stores the enum name as a plain string ('EUR', 'USD', …).
    Validates on write and returns a Currency member on read.
    """
    impl = String
    cache_ok = True

    def process_bind_param(self, value, dialect):
        """When writing to DB: accept a Currency member or a valid code string."""
        if value is None:
            return value
        if isinstance(value, Currency):
            return value.name
        member = Currency.from_code(str(value))
        if member is None:
            raise ValueError(f"Invalid currency code: {value!r}. Must be one of: {[c.name for c in Currency]}")
        return member.name

    def process_result_value(self, value, dialect):
        """When reading from DB: return a Currency enum member."""
        if value is None:
            return value
        return Currency.from_code(value)


class TradeTypeColumn(TypeDecorator):
    """Stores TradeType as its string value; returns a TradeType member on read."""
    impl = String
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if isinstance(value, TradeType):
            return value.value
        # accept raw strings that match a valid value
        valid = {m.value for m in TradeType}
        if value not in valid:
            raise ValueError(f"Invalid TradeType: {value!r}. Must be one of: {sorted(valid)}")
        return value

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        return TradeType(value)


class TransactionTypeColumn(TypeDecorator):
    """Stores TransactionType as its string value; returns a TransactionType member on read."""
    impl = String
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if isinstance(value, TransactionType):
            return value.value
        valid = {m.value for m in TransactionType}
        if value not in valid:
            raise ValueError(f"Invalid TransactionType: {value!r}. Must be one of: {sorted(valid)}")
        return value

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        return TransactionType(value)


class InstrumentCategoryColumn(TypeDecorator):
    """Stores InstrumentCategory as its string value; returns an InstrumentCategory member on read."""
    impl = String
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if isinstance(value, DistributionPolicy):
            return value.value
        valid = {m.value for m in DistributionPolicy}
        if value not in valid:
            raise ValueError(f"Invalid InstrumentCategory: {value!r}. Must be one of: {sorted(valid)}")
        return value

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        return DistributionPolicy(value)
