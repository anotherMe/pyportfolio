

# Backlog

- add a "Link" table ? I mean a FK table to store al current and future links ( JustETF, Yahoo, etc )
- cache some data; starts with account list ( used in every page )
- have a look at [AGGrid](https://www.ag-grid.com/)
- try to automate data download from Yahoo Finance ( maybe with [yfinance](https://github.com/ranaroussi/yfinance) ? )
- manage currency properly ( read the currency from price tables and enforce use of the related Enum )
- sum fee to prices inside all list and views
- add other Yahoo columns to OHLCV table ( events, dividends, etc )
- automatically calculate taxes on sell ( based on a parameter on settings ? like 26% ? )


# Ongoing

- use `logging.exception()`
- add service layer
- manage sessions locally ( avoid one session for the whole page ); maybe worth though to keep managing the session on the page, not on the lower layers
- implement Python logging ( see: logging_config.py )
- create custom Exceptions in the layer just below the UI


# Do

- implement Delete functionality
    - add "Delete" confirmation dialog for Trades and other objects that currently miss that feature
    - now delete functionality is correctly implemented in `transactions_details.py`: use it as a reference


# Doing



# Done

- manage TimeZone 
- fix current market positions using Prices instead of OHLCVs 
- when showing latest prices, read them from table Price not OHLCV
- when loading Yahoo prices, load MarketPrice too 
- add "granularity" to MarketPrice table
- restore "Price" table and models
- automatically add transactions on a trade insertion
- add market prices pages ( add it to instruments page ? )
- when loading Yahoo data, create Instrument if not existent
- manage MarketPrices / manage OHLCV: choose one table, drop the other
- missing "category" in instrument edit
- errors on "Trade edit"
- add fee's transaction when adding trade
- pre-fill "Add transaction" fields when coming from the "Trade details" page
- increase to six decimal storage of currency
- add transactions on a trade in the trade_details page
- add trades on an instrument in the instrument_details page
- from "list" page go to specific "details" ?
- introduce Account model
- working on Instruments now, align other models too
- clicking on "Delete" button gives error because one too many dialog opened
- move away from st.tabs, toward multi-page 
- ask confirmation before *delete* operations
