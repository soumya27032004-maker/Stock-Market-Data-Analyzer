"""Local educational FastAPI backend. DO NOT expose publicly: no authentication."""
from contextlib import asynccontextmanager
from pathlib import Path
import sqlite3
import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from src.config import DB_PATH, DEMO_TICKERS
from src.data import get_prices, ticker_valid
from src.indicators import compute_indicators, summarize
from src.backtest import run_sma_backtest
from src import store


class RefreshBody(BaseModel):
    source: str = "sample"
    start: str = "2024-01-01"
    end: str | None = None


class BacktestBody(BaseModel):
    ticker: str = "DEMO_AAPL"
    fee_bps: float = Field(5.0, ge=0, le=1000)
    slippage_bps: float = Field(2.0, ge=0, le=1000)
    start: str | None = None
    end: str | None = None


class TickerBody(BaseModel):
    ticker: str


class TransactionBody(BaseModel):
    ticker: str
    side: str
    qty: float = Field(gt=0)
    price: float = Field(gt=0)
    fees: float = Field(0, ge=0)


class AlertBody(BaseModel):
    ticker: str
    rule: str
    threshold: float = 0


def _analysis_for(ticker: str, db_path: Path) -> pd.DataFrame:
    ticker = ticker_valid(ticker)
    store.init_db(db_path)
    with store.connect(db_path) as con:
        rows = con.execute("""SELECT date,open,high,low,close,adj_close,volume
                FROM candles_daily WHERE ticker=? ORDER BY date""", (ticker,)).fetchall()
    if not rows:
        raise HTTPException(404, f"No data for {ticker}. Run POST /refresh/{ticker} first.")
    return compute_indicators(pd.DataFrame([dict(row) for row in rows]))


def create_app(db_path: str | Path = DB_PATH) -> FastAPI:
    db_path = Path(db_path)

    @asynccontextmanager
    async def lifespan(_app):
        store.init_db(db_path)
        for ticker in DEMO_TICKERS:
            with store.connect(db_path) as con:
                exists = con.execute("SELECT 1 FROM candles_daily WHERE ticker=? LIMIT 1", (ticker,)).fetchone()
            if not exists:
                df = compute_indicators(get_prices("sample", ticker))
                store.save_analysis(ticker, "sample", df, db_path)
                store.add_watchlist(ticker, db_path)
        yield

    app = FastAPI(title="Stock Market Data Analyzer API", version="1.0.0", lifespan=lifespan,
                  description="Demo-only local API; historical/delayed prices, never real trade orders.")

    @app.get("/health")
    def health():
        return {"ok": True, "mode": "educational", "database": str(db_path.name)}

    @app.post("/refresh/{ticker}")
    def refresh(ticker: str, body: RefreshBody):
        try:
            if body.source not in ("sample", "yahoo"):
                raise ValueError("API only permits sample and yahoo sources; use CLI for local CSV")
            frame = compute_indicators(get_prices(body.source, ticker, body.start, body.end))
            store.save_analysis(ticker, body.source, frame, db_path)
            store.add_watchlist(ticker, db_path)
            return {"ok": True, "ticker": ticker_valid(ticker), "source": body.source,
                    "rows": len(frame), "last_date": frame["date"].iloc[-1]}
        except (ValueError, RuntimeError, FileNotFoundError) as e:
            raise HTTPException(400, str(e)) from e
        except Exception as e:
            raise HTTPException(502, f"Data provider failed: {e}") from e

    @app.get("/chart/{ticker}")
    def chart(ticker: str, days: int = Query(252, ge=1, le=5000)):
        try:
            rows = store.list_chart(ticker, days, db_path)
        except ValueError as e:
            raise HTTPException(400, str(e)) from e
        if not rows:
            raise HTTPException(404, "Ticker not in database. Refresh it first.")
        return rows

    @app.get("/summary/{ticker}")
    def summary(ticker: str):
        df = _analysis_for(ticker, db_path)
        with store.connect(db_path) as con:
            source = con.execute("SELECT data_source FROM symbols WHERE ticker=?", (ticker_valid(ticker),)).fetchone()
        return summarize(df, ticker_valid(ticker), source[0] if source else "unknown")

    @app.post("/backtest/sma")
    def backtest(body: BacktestBody):
        try:
            frame = _analysis_for(body.ticker, db_path)
            result = run_sma_backtest(frame, fee_bps=body.fee_bps, slippage_bps=body.slippage_bps,
                                      start=body.start, end=body.end)
            key = store.save_backtest(body.ticker, result, body.model_dump(), db_path)
            return {"id": key, "ticker": ticker_valid(body.ticker), "stats": result}
        except ValueError as e:
            raise HTTPException(400, str(e)) from e

    @app.get("/watchlist")
    def watchlist():
        return store.list_watchlist(db_path)

    @app.post("/watchlist")
    def add_watch(body: TickerBody):
        try:
            store.add_watchlist(body.ticker, db_path)
            return {"ok": True, "ticker": ticker_valid(body.ticker)}
        except ValueError as e:
            raise HTTPException(400, str(e)) from e

    @app.delete("/watchlist/{ticker}")
    def delete_watch(ticker: str):
        store.remove_watchlist(ticker, db_path)
        return {"ok": True}

    @app.get("/portfolio/transactions")
    def all_transactions():
        return store.transactions(db_path)

    @app.get("/portfolio/positions")
    def all_positions():
        return store.positions(db_path)

    @app.post("/portfolio/transactions")
    def buy_sell(body: TransactionBody):
        try:
            key = store.add_transaction(**body.model_dump(), path=db_path)
            return {"ok": True, "id": key}
        except ValueError as e:
            raise HTTPException(400, str(e)) from e

    @app.get("/alerts")
    def alerts():
        return store.list_alerts(db_path)

    @app.get("/alerts/events")
    def events():
        return store.alert_events(db_path)

    @app.post("/alerts")
    def new_alert(body: AlertBody):
        try:
            key = store.add_alert(**body.model_dump(), path=db_path)
            return {"ok": True, "id": key}
        except ValueError as e:
            raise HTTPException(400, str(e)) from e

    @app.post("/alerts/check")
    def evaluate():
        return {"events": store.check_alerts(db_path),
                "message": "Manual local alerts only; no messages are sent outside this computer."}

    return app


app = create_app()
