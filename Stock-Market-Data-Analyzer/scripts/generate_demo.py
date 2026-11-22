"""Reproducible SYNTHETIC daily OHLCV; not actual AAPL/NVDA/RELIANCE quotes.

Run: python scripts/generate_demo.py
"""
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "data" / "sample"
DEST.mkdir(parents=True, exist_ok=True)
DATES = pd.bdate_range("2024-01-02", "2026-11-20")
SPECS = [
    ("DEMO_AAPL", 140.0, 0.00035, 0.014, 7),
    ("DEMO_NVDA", 250.0, 0.00065, 0.026, 22),
    ("DEMO_RELIANCE", 1550.0, 0.00020, 0.018, 123),
]

for symbol, start, drift, volatility, seed in SPECS:
    rng = np.random.default_rng(seed)
    # Regimes increase/decrease within the series to make crossover interesting.
    regime = 0.0008 * np.sin(np.linspace(0, 13 * np.pi, len(DATES)))
    log_return = drift + regime + rng.normal(0, volatility, len(DATES))
    base_close = start * np.exp(np.cumsum(log_return))
    overnight = rng.normal(0, volatility * 0.25, len(DATES))
    opens = base_close * np.exp(overnight)
    highs = np.maximum(opens, base_close) * (1 + rng.uniform(0.001, 0.018, len(DATES)))
    lows = np.minimum(opens, base_close) * (1 - rng.uniform(0.001, 0.018, len(DATES)))
    volumes = rng.integers(1_500_000, 9_000_000, len(DATES))
    # Same as close; synthetic data intentionally has no dividends or splits.
    df = pd.DataFrame({"Date": DATES.strftime("%Y-%m-%d"), "Open": opens,
                       "High": highs, "Low": lows, "Close": base_close,
                       "Adj Close": base_close, "Volume": volumes})
    df.to_csv(DEST / f"{symbol}.csv", index=False, float_format="%.6f")
    print(f"Wrote {symbol} ({len(df)} synthetic trading days)")
