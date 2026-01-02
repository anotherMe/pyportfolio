

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

- add some other type of categorization in Instruments:
    - ETF vs stocks
    - Bond ETF vs Equity ETF vs ETC
    

- add all transactions (fee, div and taxes ) in totals ( eg: Portfolio overview )
    - add a "transactions" column ?
    - change sign of Transaction amount ( already existent and when adding )

- the "Add/Edit" page doesn't work as expected


# Doing

- Position refactoring

    - [X] Transaction is no longer linked to Trade but to Position
    - [X] Trade is linked to Position as well
    - [ ] when to add a new Position ? create explicitly or create when creating a buy trade ?
    - [ ] show/calculate transactions amount in "Positions list"
    - [X] Positions list must be rewritten: now it's an actual list of Positions
    - [ ] sum "Realized PnL" and "Unrealized PnL" in "Positions list" page ?
    - [ ] Add a "Position detail" page


# Done
