
import yfinance as yf

dat = yf.Ticker("IEGE.MI")
# dat.info
# dat.calendar
# dat.analyst_price_targets
# dat.quarterly_income_stmt
dat.history(period='1mo')
# dat.option_chain(dat.options[0]).calls

# tickers = yf.Tickers('MSFT AAPL GOOG')
# tickers.tickers['MSFT'].info
# yf.download(['MSFT', 'AAPL', 'GOOG'], period='1mo')
print("hello")