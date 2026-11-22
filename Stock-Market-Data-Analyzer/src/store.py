"""Small SQLite persistence layer; parameterized queries only."""
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
import uuid
import math
import pandas as pd
from .config import DB_PATH, ROOT
from .data import ticker_valid


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def connect(path: str | Path = DB_PATH):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys=ON")
    return con


def init_db(path: str | Path = DB_PATH):
    with connect(path) as con:
        con.executescript((ROOT / "db" / "schema.sql").read_text(encoding="utf-8"))


def _sql_num(x):
    return None if x is None or (isinstance(x, float) and not math.isfinite(x)) or pd.isna(x) else float(x)


def save_analysis(ticker: str, source: str, frame: pd.DataFrame, path: str | Path = DB_PATH):
    ticker = ticker_valid(ticker)
    init_db(path)
    candle_fields = ["open", "high", "low", "close", "adj_close", "volume"]
    indicator_fields = ["sma20", "sma50", "rsi14", "macd", "macd_signal", "macd_hist",
                        "bb_upper", "bb_mid", "bb_lower", "daily_return", "rolling_vol20"]
    candles = [(ticker, r["date"], *(_sql_num(r[c]) for c in candle_fields)) for _, r in frame.iterrows()]
    indicators = [(ticker, r["date"], *(_sql_num(r[c]) for c in indicator_fields), r["signal"])
                  for _, r in frame.iterrows()]
    with connect(path) as con:
        con.execute("INSERT OR REPLACE INTO symbols(ticker,name,data_source) VALUES (?,?,?)",
                    (ticker, ticker, source))
        con.executemany("""INSERT OR REPLACE INTO candles_daily
            (ticker,date,open,high,low,close,adj_close,volume) VALUES(?,?,?,?,?,?,?,?)""", candles)
        con.executemany("""INSERT OR REPLACE INTO indicators_daily
            (ticker,date,sma20,sma50,rsi14,macd,macd_signal,macd_hist,bb_upper,
             bb_mid,bb_lower,daily_return,rolling_vol20,signal)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", indicators)


def list_chart(ticker: str, days: int = 252, path: str | Path = DB_PATH) -> list[dict]:
    if not Path(path).exists():
        return []
    with connect(path) as con:
        rows = con.execute("""SELECT c.date,c.open,c.high,c.low,c.close,c.adj_close,c.volume,
              i.sma20,i.sma50,i.rsi14,i.macd,i.bb_upper,i.bb_lower,i.daily_return,i.signal
            FROM candles_daily c LEFT JOIN indicators_daily i
            ON c.ticker=i.ticker AND c.date=i.date
            WHERE c.ticker=? ORDER BY c.date DESC LIMIT ?""",
            (ticker_valid(ticker), max(1, min(days, 5000)))).fetchall()
    return [dict(r) for r in reversed(rows)]


def save_backtest(ticker: str, stats: dict, params: dict, path: str | Path = DB_PATH) -> str:
    init_db(path)
    key = str(uuid.uuid4())
    with connect(path) as con:
        con.execute("""INSERT INTO backtests
          (id,ticker,name,params_json,first_date,last_date,total_return,max_drawdown,sharpe,trades,win_rate,created_at)
          VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
          (key, ticker_valid(ticker), "SMA20/50 delayed crossover", json.dumps(params),
           stats["first_date"], stats["last_date"], stats["total_return"], stats["max_drawdown"],
           stats["sharpe"], stats["trades"], stats["win_rate"], utc_now()))
    return key


def list_watchlist(path: str | Path = DB_PATH) -> list[str]:
    init_db(path)
    with connect(path) as con:
        rows = con.execute("SELECT ticker FROM watchlist ORDER BY ticker").fetchall()
    return [r[0] for r in rows]


def add_watchlist(ticker: str, path: str | Path = DB_PATH):
    init_db(path)
    with connect(path) as con:
        con.execute("INSERT OR IGNORE INTO watchlist(ticker,created_at) VALUES (?,?)",
                    (ticker_valid(ticker), utc_now()))


def remove_watchlist(ticker: str, path: str | Path = DB_PATH):
    init_db(path)
    with connect(path) as con:
        con.execute("DELETE FROM watchlist WHERE ticker=?", (ticker_valid(ticker),))


def _positions(con) -> list[dict]:
    txs = con.execute("SELECT * FROM portfolio_tx ORDER BY ts,rowid").fetchall()
    # The cost basis is a moving-weighted-average approximation, not tax-lot accounting.
    portfolio = {}
    for tx in txs:
        key = tx["ticker"]
        d = portfolio.setdefault(key, {"ticker": key, "quantity": 0.0, "cost_basis": 0.0,
                                      "realized_pnl": 0.0})
        q, price, fees = tx["qty"], tx["price"], tx["fees"]
        if tx["side"] == "BUY":
            d["quantity"] += q
            d["cost_basis"] += q * price + fees
        else:
            if q > d["quantity"] + 1e-9:
                raise ValueError(f"Invalid transaction history: oversold {key}")
            avg = d["cost_basis"] / d["quantity"] if d["quantity"] else 0
            d["realized_pnl"] += q * (price - avg) - fees
            d["cost_basis"] -= q * avg
            d["quantity"] -= q
            if d["quantity"] < 1e-9:
                d["quantity"] = 0.0
                d["cost_basis"] = 0.0
    for d in portfolio.values():
        d["average_cost"] = d["cost_basis"] / d["quantity"] if d["quantity"] else 0.0
    return sorted(portfolio.values(), key=lambda x: x["ticker"])


def positions(path: str | Path = DB_PATH) -> list[dict]:
    init_db(path)
    with connect(path) as con:
        return _positions(con)


def transactions(path: str | Path = DB_PATH) -> list[dict]:
    init_db(path)
    with connect(path) as con:
        return [dict(x) for x in con.execute("SELECT * FROM portfolio_tx ORDER BY ts DESC,rowid DESC")]


def add_transaction(ticker: str, side: str, qty: float, price: float, fees: float = 0,
                    path: str | Path = DB_PATH, ts: str | None = None) -> str:
    ticker = ticker_valid(ticker)
    side = side.upper()
    if side not in ("BUY", "SELL") or qty <= 0 or price <= 0 or fees < 0:
        raise ValueError("Use BUY/SELL, positive quantity and price, and nonnegative fees.")
    if not all(math.isfinite(v) for v in (qty, price, fees)):
        raise ValueError("Quantity, price and fees must be finite.")
    init_db(path)
    tx_id = str(uuid.uuid4())
    with connect(path) as con:
        if side == "SELL":
            available = next((p["quantity"] for p in _positions(con) if p["ticker"] == ticker), 0)
            if qty > available + 1e-9:
                raise ValueError(f"Cannot sell {qty}; only {available:g} {ticker} shares held.")
        con.execute("""INSERT INTO portfolio_tx(id,ticker,ts,side,qty,price,fees)
                   VALUES(?,?,?,?,?,?,?)""",
                   (tx_id, ticker, ts or utc_now(), side, qty, price, fees))
    return tx_id

VALID_RULES = ("CLOSE_ABOVE", "CLOSE_BELOW", "RSI_BELOW", "RSI_ABOVE", "CLOSE_LT_BBLOWER")


def add_alert(ticker: str, rule: str, threshold: float = 0, path: str | Path = DB_PATH) -> str:
    ticker = ticker_valid(ticker)
    rule = rule.upper()
    if rule not in VALID_RULES or not math.isfinite(threshold):
        raise ValueError(f"Rule must be one of {', '.join(VALID_RULES)} and threshold finite.")
    key = str(uuid.uuid4())
    init_db(path)
    with connect(path) as con:
        con.execute("INSERT INTO alerts(id,ticker,rule,threshold) VALUES (?,?,?,?)",
                    (key, ticker, rule, threshold))
    return key


def list_alerts(path: str | Path = DB_PATH) -> list[dict]:
    init_db(path)
    with connect(path) as con:
        return [dict(x) for x in con.execute("SELECT * FROM alerts ORDER BY ticker,rule")]


def alert_events(path: str | Path = DB_PATH) -> list[dict]:
    init_db(path)
    with connect(path) as con:
        return [dict(x) for x in con.execute("SELECT * FROM alert_events ORDER BY date DESC")]


def check_alerts(path: str | Path = DB_PATH) -> list[dict]:
    """Evaluate last stored daily candle. Fires once per rule per trading date.

    Local alerts only; to send messages, add authenticated mail provider integration.
    """
    init_db(path)
    fired = []
    with connect(path) as con:
        for a in con.execute("SELECT * FROM alerts WHERE active=1").fetchall():
            d = con.execute("""SELECT c.date,c.adj_close,i.rsi14,i.bb_lower FROM candles_daily c
               LEFT JOIN indicators_daily i ON c.ticker=i.ticker AND c.date=i.date
               WHERE c.ticker=? ORDER BY c.date DESC LIMIT 1""", (a["ticker"],)).fetchone()
            if not d or a["last_fired_date"] == d["date"]:
                continue
            value = {"CLOSE_ABOVE": d["adj_close"], "CLOSE_BELOW": d["adj_close"],
                     "RSI_BELOW": d["rsi14"], "RSI_ABOVE": d["rsi14"],
                     "CLOSE_LT_BBLOWER": d["adj_close"]}[a["rule"]]
            rule = a["rule"]
            ok = value is not None and (
                (rule == "CLOSE_ABOVE" and value > a["threshold"]) or
                (rule == "CLOSE_BELOW" and value < a["threshold"]) or
                (rule == "RSI_BELOW" and value < a["threshold"]) or
                (rule == "RSI_ABOVE" and value > a["threshold"]) or
                (rule == "CLOSE_LT_BBLOWER" and d["bb_lower"] is not None and value < d["bb_lower"]))
            if ok:
                msg = f"{a['ticker']} {rule} triggered on {d['date']} (value={value:.2f})"
                event = {"id": str(uuid.uuid4()), "alert_id": a["id"], "ticker": a["ticker"],
                         "date": d["date"], "message": msg}
                con.execute("""INSERT OR IGNORE INTO alert_events(id,alert_id,ticker,date,message)
                                VALUES(?,?,?,?,?)""", tuple(event.values()))
                con.execute("UPDATE alerts SET last_fired_date=? WHERE id=?", (d["date"], a["id"]))
                fired.append(event)
    return fired
