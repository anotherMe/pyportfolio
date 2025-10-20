

# Backlog

- add link to JustETF ( for ETFs ); maybe worth adding a dedicated table ?
- cache some data; starts with account list ( used in every page )
- clicking on "Delete" button gives error because one too many dialog opened ( solved but sub-optimally)
- automatically add transactions on a trade insertion ?
- add market prices pages ( add it to instruments page ? )
- in the portfolio_repository.py functions, must add the Account variable ( eg: sell and buy in the same account )

# Do

- sum fee to prices inside all list and views
- missing "category" in instrument edit

# Doing

# Done

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