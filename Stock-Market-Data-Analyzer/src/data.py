"""Load, validate, and clean daily OHLCV price data.

Yahoo data is an unofficial public-data feed; it can be delayed/unavailable.
The included CSV files are entirely synthetic and clearly labeled DEMO.
"""
from pathlib import Path
import re
import pandas as pd
from .config import SAMPLE_DIR

REQUIRED = ("date", "open", "high", "low", "close", "volume")
STOCK_PATTERN = re.compile(r"^[A-Z0-9^._=-]{1,24}$")


def ticker_valid(ticker: str) -> str:
    clean = str(ticker).strip().upper()
    if not STOCK_PATTERN.fullmatch(clean):
        raise ValueError("Invalid ticker. Use letters/numbers and . - _ = ^ only (up to 24).")
    return clean


def clean_prices(frame: pd.DataFrame) -> pd.DataFrame:
    """Normalize columns; discard corrupt, missing or duplicate trading rows.

    Never forward-fill missing prices: doing so fabricates zero-return days.
    """
    if frame is None or frame.empty:
        raise ValueError("No price rows were returned. Check the symbol, range, or CSV.")
    df = frame.copy()
    # Single-ticker yfinance downloads can still have a MultiIndex.
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    if "date" not in [str(x).strip().lower() for x in df.columns] and isinstance(df.index, pd.DatetimeIndex):
        df = df.reset_index()
    df.columns = [str(x).strip().lower().replace(" ", "_") for x in df.columns]
    if "datetime" in df.columns and "date" not in df.columns:
        df = df.rename(columns={"datetime": "date"})
    if "adjclose" in df.columns and "adj_close" not in df.columns:
        df = df.rename(columns={"adjclose": "adj_close"})
    missing = sorted(set(REQUIRED) - set(df.columns))
    if missing:
        raise ValueError(f"CSV/data is missing required columns: {', '.join(missing)}")
    # Coerce timezone aware timestamps to calendar date without local timezone shift.
    df["date"] = pd.to_datetime(df["date"], errors="coerce", utc=True).dt.strftime("%Y-%m-%d")
    if "adj_close" not in df.columns:
        df["adj_close"] = df["close"]
    for col in ("open", "high", "low", "close", "adj_close", "volume"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=["date", *REQUIRED[1:], "adj_close"])
    # Avoid invalid or nonsensical OHLC before de-duplication, so a corrupt
    # later duplicate cannot replace a valid earlier observation.
    # Missing trading days are allowed.
    ok = (df[["open", "high", "low", "close", "adj_close"]] > 0).all(axis=1)
    ok &= df["volume"] >= 0
    ok &= df["high"] >= df[["open", "low", "close"]].max(axis=1)
    ok &= df["low"] <= df[["open", "high", "close"]].min(axis=1)
    result = df.loc[ok, ["date", "open", "high", "low", "close", "adj_close", "volume"]]
    result = result.drop_duplicates(subset="date", keep="last").sort_values("date").reset_index(drop=True)
    if len(result) < 55:
        raise ValueError(f"Only {len(result)} valid rows; need at least 55 for SMA50 & backtest.")
    return result


def from_csv(path: str | Path) -> pd.DataFrame:
    file_path = Path(path)
    if not file_path.is_file():
        raise FileNotFoundError(f"CSV not found: {file_path}")
    return clean_prices(pd.read_csv(file_path))


def from_demo(ticker: str = "DEMO_AAPL") -> pd.DataFrame:
    ticker = ticker_valid(ticker)
    path = SAMPLE_DIR / f"{ticker}.csv"
    if not path.is_file():
        raise FileNotFoundError(f"No demo file named {path.name}. Choose DEMO_AAPL, DEMO_NVDA or DEMO_RELIANCE.")
    return from_csv(path)


def from_yahoo(ticker: str, start: str, end: str | None = None) -> pd.DataFrame:
    ticker = ticker_valid(ticker)
    try:
        import yfinance as yf  # optional when running the offline sample
    except ImportError as ex:
        raise RuntimeError("Install yfinance with: python -m pip install -r requirements.txt") from ex
    # Explicit flags matter: yfinance defaults changed and multi-level columns
    # can appear for even a single ticker. Request unadjusted OHLC + Adj Close.
    kwargs = dict(tickers=ticker, start=start, end=end, auto_adjust=False, progress=False, threads=False)
    try:
        raw = yf.download(**kwargs, multi_level_index=False)
    except TypeError:  # older yfinance versions
        raw = yf.download(**kwargs)
    if raw is None or raw.empty:
        raise ValueError(f"Yahoo returned no prices for {ticker}. Try another date/symbol or sample mode.")
    return clean_prices(raw)


def get_prices(source: str, ticker: str, start: str = "2024-01-01", end: str | None = None,
               file: str | Path | None = None) -> pd.DataFrame:
    if source == "sample":
        return from_demo(ticker)
    if source == "csv":
        if file is None:
            raise ValueError("For --source csv, add --file path/to/prices.csv")
        return from_csv(file)
    if source == "yahoo":
        return from_yahoo(ticker, start, end)
    raise ValueError("Source must be one of: sample, csv, yahoo")
