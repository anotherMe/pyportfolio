from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from core.cors import setup_cors
from routers import (
    overview,
    accounts,
    instruments,
    trades,
    transactions,
    prices,
    other,
)


app = FastAPI(title="My Portfolio Dashboard")
setup_cors(app)

app.include_router(overview.router, prefix="/api/overview", tags=["Overview"])
app.include_router(accounts.router, prefix="/api/accounts", tags=["Accounts"])
app.include_router(instruments.router, prefix="/api/instruments", tags=["Instruments"])
app.include_router(trades.router, prefix="/api/trades", tags=["Trades"])
app.include_router(transactions.router, prefix="/api/transactions", tags=["Transactions"])
app.include_router(prices.router, prefix="/api/prices", tags=["Prices"])
app.include_router(other.router, prefix="/api/other", tags=["Other"])


# TODO: This is an API, we should point to the swagger instead ?
@app.get("/", response_class=HTMLResponse)
def index():
    """Main dashboard landing page."""
    html = """
    <html>
        <head><title>My Portfolio Dashboard</title></head>
        <body>
            <h1>My Portfolio Dashboard</h1>
        </body>
    </html>
    """
    return html
