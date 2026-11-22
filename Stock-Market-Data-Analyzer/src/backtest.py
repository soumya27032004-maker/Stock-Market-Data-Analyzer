"""Educational daily-bar, long-only SMA20/50 simulation.

Signals are computed from close[t], position for return[t+1] is determined by
signal[t] via shift(1). Includes fees/slippage when position changes.
No execution at an actual market open is simulated; trade prices are simplified.
"""
import numpy as np
import pandas as pd
from .config import TRADING_DAYS


def run_sma_backtest(frame: pd.DataFrame, fee_bps: float = 5, slippage_bps: float = 2,
                     start: str | None = None, end: str | None = None) -> dict:
    if fee_bps < 0 or slippage_bps < 0:
        raise ValueError("Fees and slippage cannot be negative.")
    # Compute indicators over all history BEFORE slicing to retain proper warm-up.
    df = frame.dropna(subset=["sma20", "sma50"]).copy().reset_index(drop=True)
    if start:
        df = df[df["date"] >= start]
    if end:
        df = df[df["date"] <= end]
    df = df.reset_index(drop=True)
    if len(df) < 10:
        raise ValueError("Backtest requires at least 10 days after SMA warmup/date filtering.")
    desired_position = (df["sma20"] > df["sma50"]).astype(int)
    actual_position = desired_position.shift(1).fillna(0).astype(int)
    # At start of window, do not secretly inherit earlier signal exposure.
    changes = actual_position.diff().fillna(actual_position.iloc[0]).abs()
    daily_market = df["adj_close"].pct_change().fillna(0)
    trading_cost = changes * ((fee_bps + slippage_bps) / 10000)
    daily_strategy = actual_position * daily_market - trading_cost
    strategy = (1 + daily_strategy).cumprod()
    benchmark = (1 + daily_market).cumprod()
    dd = strategy / strategy.cummax() - 1
    std = daily_strategy.std(ddof=1)
    sharpe = (daily_strategy.mean() / std * np.sqrt(TRADING_DAYS)) if std > 0 else None
    entries = (actual_position.diff().fillna(actual_position).eq(1))
    exits = (actual_position.diff().fillna(actual_position).eq(-1))
    # Win-rate is on CLOSED trades (not execution days), net of fees.
    completed = []
    trade_factor = None
    for pos, enter, leave, daily_r in zip(actual_position, entries, exits, daily_strategy):
        if enter:
            trade_factor = 1.0
        if trade_factor is not None:
            trade_factor *= 1 + daily_r
        if leave and trade_factor is not None:
            completed.append(trade_factor - 1)
            trade_factor = None
    result = {
        "first_date": str(df["date"].iloc[0]), "last_date": str(df["date"].iloc[-1]),
        "total_return": float(strategy.iloc[-1] - 1),
        "buy_hold_return": float(benchmark.iloc[-1] - 1),
        "max_drawdown": float(dd.min()), "sharpe": float(sharpe) if sharpe is not None else None,
        "trades": int(entries.sum()), "closed_trades": len(completed),
        "win_rate": float(np.mean(np.array(completed) > 0)) if completed else None,
        "fee_bps": float(fee_bps), "slippage_bps": float(slippage_bps),
        "note": "Simplified close-to-close simulation, delayed signal, no taxes/market impact. Educational only.",
        "curve": [{"date": str(date), "strategy": float(s), "buy_hold": float(b)}
                  for date, s, b in zip(df["date"], strategy, benchmark)]
    }
    return result
