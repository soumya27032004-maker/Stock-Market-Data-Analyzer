"""Simple price-based indicators built with Pandas (no paid service)."""
import numpy as np
import pandas as pd
from .config import TRADING_DAYS


def compute_indicators(prices: pd.DataFrame) -> pd.DataFrame:
    df = prices.copy().sort_values("date").reset_index(drop=True)
    p = df["adj_close"].astype(float)
    df["daily_return"] = p.pct_change()
    df["sma20"] = p.rolling(20, min_periods=20).mean()
    df["sma50"] = p.rolling(50, min_periods=50).mean()
    change = p.diff()
    up = change.clip(lower=0)
    down = -change.clip(upper=0)
    # Wilder's RSI: seed with simple average of first 14 gains/losses.
    gain_seed = up.rolling(14, min_periods=14).mean()
    loss_seed = down.rolling(14, min_periods=14).mean()
    avg_gain = np.full(len(p), np.nan)
    avg_loss = np.full(len(p), np.nan)
    if len(p) > 14:
        avg_gain[14], avg_loss[14] = gain_seed.iloc[14], loss_seed.iloc[14]
        for i in range(15, len(p)):
            avg_gain[i] = (avg_gain[i-1] * 13 + up.iloc[i]) / 14
            avg_loss[i] = (avg_loss[i-1] * 13 + down.iloc[i]) / 14
    ratio = pd.Series(avg_gain) / pd.Series(avg_loss).replace(0, np.nan)
    df["rsi14"] = 100 - (100 / (1 + ratio))
    df.loc[(pd.Series(avg_loss) == 0) & (pd.Series(avg_gain) > 0), "rsi14"] = 100.0
    df.loc[(pd.Series(avg_gain) == 0) & (pd.Series(avg_loss) == 0), "rsi14"] = 50.0
    fast = p.ewm(span=12, adjust=False).mean()
    slow = p.ewm(span=26, adjust=False).mean()
    df["macd"] = fast - slow
    df["macd_signal"] = df["macd"].ewm(span=9, adjust=False).mean()
    df["macd_hist"] = df["macd"] - df["macd_signal"]
    df["bb_mid"] = p.rolling(20, min_periods=20).mean()
    std = p.rolling(20, min_periods=20).std(ddof=0)
    df["bb_upper"] = df["bb_mid"] + 2 * std
    df["bb_lower"] = df["bb_mid"] - 2 * std
    df["rolling_vol20"] = df["daily_return"].rolling(20).std() * np.sqrt(TRADING_DAYS)
    # Crossover event, not a financial recommendation.
    regime = df["sma20"] > df["sma50"]
    prior_valid = df["sma20"].shift(1).notna() & df["sma50"].shift(1).notna()
    df["signal"] = np.select([prior_valid & regime & ~regime.shift(1, fill_value=False),
                              prior_valid & ~regime & regime.shift(1, fill_value=False)],
                             ["CROSS_UP", "CROSS_DOWN"], default="NONE")
    return df


def summarize(df: pd.DataFrame, ticker: str, source: str) -> dict:
    p = df["adj_close"]
    returns = df["daily_return"].dropna()
    annual_vol = float(returns.std() * np.sqrt(TRADING_DAYS)) if len(returns) > 1 else None
    ma20 = df["sma20"].iloc[-1]
    ma50 = df["sma50"].iloc[-1]
    current = "Above SMA20 & SMA50" if p.iloc[-1] > ma20 and p.iloc[-1] > ma50 else (
        "Below SMA20 & SMA50" if p.iloc[-1] < ma20 and p.iloc[-1] < ma50 else "Mixed")
    return {
        "ticker": ticker, "source": source, "first_date": df["date"].iloc[0], "last_date": df["date"].iloc[-1],
        "rows": int(len(df)), "first_adj_close": float(p.iloc[0]), "last_adj_close": float(p.iloc[-1]),
        "price_change_pct": float((p.iloc[-1] / p.iloc[0] - 1) * 100),
        "daily_avg_return_pct": float(returns.mean() * 100),
        "annual_volatility_pct": annual_vol * 100 if annual_vol is not None else None,
        "highest_raw_high": float(df["high"].max()), "lowest_raw_low": float(df["low"].min()),
        "sma20": float(ma20) if pd.notna(ma20) else None,
        "sma50": float(ma50) if pd.notna(ma50) else None,
        "rsi14": float(df["rsi14"].iloc[-1]) if pd.notna(df["rsi14"].iloc[-1]) else None,
        "trend_observation": current,
        "latest_crossover": str(df.loc[df["signal"] != "NONE", "signal"].iloc[-1]) if (df["signal"] != "NONE").any() else "NONE",
        "currency_note": "Use the original ticker exchange/currency; synthetic demo units are arbitrary.",
        "warning": "Educational historical analysis, not investment advice. Past results do not predict future returns."
    }
