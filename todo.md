

# Backlog

- add a "Link" table ? I mean a FK table to store al current and future links ( JustETF, Yahoo, etc )
- cache some data; starts with account list ( used in every page )
- manage currency properly ( read the currency from price tables and enforce use of the related Enum )
- sum fee to prices inside all list and views
- add other Yahoo columns to OHLCV table ( events, dividends, etc )
- automatically calculate taxes on sell ( based on a parameter on settings ? like 26% ? )


# Ongoing

- import setup_logger
- use `logging.exception()`
- add service layer
- manage sessions locally ( avoid one session for the whole page ); maybe worth though to keep managing the session on the page, not on the lower layers
- implement Python logging ( see: logging_config.py )
- create custom Exceptions in the layer just below the UI
- add "Clear search" button ( see Instrument list page )


# Do

- still missing the "Add new Position" function
- add some other type of categorization in Instruments:
    - ETF vs stocks
    - Bond ETF vs Equity ETF vs ETC
- add fancy prices chart in "Position detail" page
- Add yearly PnL to "Position detail" page
- set the default page to "Positions list"
- add Instrument filtering to "Position list" page

- remove "account_id" column from Trade table ( leave it in Transaction table for general expenses )


# Doing

- Remove "instrument_id" from Trade
- Remove "Trades list" and "Transaction list" pages ( I mean, move the st.dataframe code to the positions page, comprising of the selection mechanics )
- Trades can no longer being added standalone ( it doesn't make sense to select a Position ); only adding Trades aftering selecting a Position should be allowed

# Done
