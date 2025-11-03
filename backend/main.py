from fastapi import FastAPI
from fastapi.responses import HTMLResponse
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

app.include_router(overview.router, prefix="/overview", tags=["Overview"])
app.include_router(accounts.router, prefix="/accounts", tags=["Accounts"])
app.include_router(instruments.router, prefix="/instruments", tags=["Instruments"])
app.include_router(trades.router, prefix="/trades", tags=["Trades"])
app.include_router(transactions.router, prefix="/transactions", tags=["Transactions"])
app.include_router(prices.router, prefix="/prices", tags=["Prices"])
app.include_router(other.router, prefix="/other", tags=["Other"])


@app.get("/", response_class=HTMLResponse)
def index():
    """Main dashboard landing page."""
    html = """
    <html>
        <head><title>My Portfolio Dashboard</title></head>
        <body>
            <h1>My Portfolio Dashboard</h1>
            <ul>
                <li><a href="/overview">Overview</a></li>
                <li><a href="/accounts">Accounts</a></li>
                <li><a href="/instruments">Instruments</a></li>
                <li><a href="/trades">Trades</a></li>
                <li><a href="/transactions">Transactions</a></li>
                <li><a href="/prices">Prices</a></li>
                <li><a href="/other">Other</a></li>
            </ul>
        </body>
    </html>
    """
    return html
