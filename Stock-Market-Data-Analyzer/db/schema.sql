-- All prices are daily; one record per ticker/date.
CREATE TABLE IF NOT EXISTS symbols (
  ticker TEXT PRIMARY KEY, name TEXT, exchange TEXT, currency TEXT, data_source TEXT
);
CREATE TABLE IF NOT EXISTS candles_daily (
  ticker TEXT NOT NULL, date TEXT NOT NULL,
  open REAL, high REAL, low REAL, close REAL, adj_close REAL, volume INTEGER,
  PRIMARY KEY (ticker, date)
);
CREATE TABLE IF NOT EXISTS indicators_daily (
  ticker TEXT NOT NULL, date TEXT NOT NULL,
  sma20 REAL, sma50 REAL, rsi14 REAL, macd REAL, macd_signal REAL, macd_hist REAL,
  bb_upper REAL, bb_mid REAL, bb_lower REAL, daily_return REAL, rolling_vol20 REAL, signal TEXT,
  PRIMARY KEY(ticker, date)
);
CREATE TABLE IF NOT EXISTS backtests (
  id TEXT PRIMARY KEY, ticker TEXT, name TEXT, params_json TEXT,
  first_date TEXT, last_date TEXT, total_return REAL, max_drawdown REAL,
  sharpe REAL, trades INTEGER, win_rate REAL, created_at TEXT
);
CREATE TABLE IF NOT EXISTS portfolio_tx (
  id TEXT PRIMARY KEY, ticker TEXT NOT NULL, ts TEXT NOT NULL,
  side TEXT NOT NULL CHECK(side IN ('BUY','SELL')),
  qty REAL NOT NULL CHECK(qty>0), price REAL NOT NULL CHECK(price>0),
  fees REAL NOT NULL DEFAULT 0 CHECK(fees>=0)
);
CREATE TABLE IF NOT EXISTS watchlist (
  ticker TEXT PRIMARY KEY, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS alerts (
  id TEXT PRIMARY KEY, ticker TEXT NOT NULL,
  rule TEXT NOT NULL, threshold REAL NOT NULL,
  active INTEGER NOT NULL DEFAULT 1, last_fired_date TEXT
);
CREATE TABLE IF NOT EXISTS alert_events (
  id TEXT PRIMARY KEY, alert_id TEXT NOT NULL, ticker TEXT NOT NULL,
  date TEXT NOT NULL, message TEXT NOT NULL,
  UNIQUE(alert_id,date)
);
