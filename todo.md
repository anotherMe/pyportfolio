
- merge instrument.name field with instrument.name_long field ( and then remove the remaining one )
- manage currency properly ( read the currency from price tables and enforce use of the related Enum )
- add other Yahoo columns to OHLCV table ( events, dividends, etc ...; see project Plasteroid )
- add other categories to Instrument ( eg: region, sector, etc ...; see JustETF for reference )
- add line chart ( or similar ) in "Dashboard" page that shows prices for the current instrument compared with another instrument selected as a benchmark; would be nice to add also buy and sell events to the timeline
- Add yearly PnL to "Position detail" page
- positions.closed and positions.closing_date are NOT currently used: should we drop them ? by deciding to keep ( and maintain ! ) those fields could get rid of the related computation logic
