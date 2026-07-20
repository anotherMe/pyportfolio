# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

pyportfolio is a Streamlit app for tracking a personal investment portfolio (accounts, instruments, positions, trades, transactions, and historical prices pulled from Yahoo Finance).

## Setup & running

```sh
source .venv/bin/activate
pip install -r requirements.txt
streamlit run main.py
```

Requires a `settings.json` at the repo root (gitignored; see `settings.json.example`) with a `database.url` SQLAlchemy connection string and an `app.default_timezone` IANA zone name (used by `lib/settings_manager.get_timezone`).

## Tests

```sh
pytest
```

Single test: `pytest tests/yahoo_finance_service_test.py::test_download_history_success`

Tests live in `tests/`. `python.testing.pytestArgs` is already set to `["tests"]` in `.vscode/settings.json`.

## Architecture

Three-layer separation, always respected in that order — pages never talk to the repo layer or to SQLAlchemy models directly, and repos never contain business logic:

1. **`lib/repo/*_repository.py`** — pure data access. Plain functions taking a SQLAlchemy `session` plus primitives, returning SQLAlchemy model instances (`lib/models.py`). No Pydantic, no business rules.
2. **`service/*_service.py`** — business logic, one `XxxService` class per domain (`AccountsService`, `PositionsService`, `OhlcvsService`, etc.). Services call repo functions, then convert models to Pydantic DTOs (`service/dtos.py`) for anything returned to the presentation layer. `PositionsService` in particular performs FIFO cost-basis matching across trades to compute realized/unrealized P&L (see `_apply_fifo` in `service/positions_service.py`).
3. **`pages/*.py`** — Streamlit UI only. Opens a session via `get_session()`, calls a service, renders DTOs. Each `*_list.py` page pairs with an `*_edit.py` page; navigation between them goes through `st.session_state["<entity>_id"]` + `st.switch_page(...)`.

`main.py` registers all pages via `st.Page`/`st.navigation` and renders the sidebar (including the account selector from `service/utils.account_selector`).

### Money and dates

- All monetary amounts are stored in the DB as integers (`write_to_db`/`read_from_db` in `lib/database.py` multiply/divide by 1,000,000). Repos and models work in these integer "micro-units"; services convert to/from float via `read_from_db`/`write_to_db` at the boundary. Never store or compare raw floats in the DB layer.
- All datetimes in the DB are UTC, enforced by the `UTCDateTime` TypeDecorator in `lib/types.py`, which rejects naive datetimes on write. Convert to local time for display only, via `service/utils.to_local` (uses `get_timezone()`).
- Enum-backed columns (`Currency`, `TradeType`, `TransactionType`, `DistributionPolicy`, `AssetClass`) each have a matching `TypeDecorator` in `lib/types.py` that validates on write and returns the enum member on read — extend that file, not the model, when adding a new enum-backed column.

### DTOs (`service/dtos.py`)

One DTO group per domain entity, generally a `XxxDTO` (read, often `model_config = {"from_attributes": True}` for `model_validate`) and an `XxxCreateDTO` (write/input). Denormalized "list" DTOs like `TradeDTO` and `TransactionDTO` implement `from_model(...)` classmethods that pull in related account/instrument fields for display, rather than joining in the page layer.

### Yahoo Finance integration

`service/YahooFinanceService.py` wraps `yfinance` to download OHLCV history for an `Instrument` (by ticker) and persist it via `lib/repo/ohlcvs_repository.py`. `service/myYahooFinanceService.py` (`YahooSymbolParser`/`YahooSymbol`) parses manually-exported Yahoo Finance JSON files as a fallback data source. Network-touching code should stay mockable at the `yfinance.Ticker` boundary, as done in `tests/yahoo_finance_service_test.py`.

### Database engine lifecycle

`lib/database.get_session()` lazily initializes a module-level SQLAlchemy engine/sessionmaker from `settings.json` (`init_engine()`), and re-initializes only if the configured DB path changes — relevant if you add settings-editing UI (see `pages/settings.py`) that can change `database.url` at runtime.

## Logging

Use `logging_config.setup_logger(__name__)` (not the stdlib `logging` module directly) to get a configured stdout logger consistent with the rest of the codebase.
