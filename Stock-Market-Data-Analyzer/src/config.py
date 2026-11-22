"""Shared application paths and default values."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SAMPLE_DIR = ROOT / "data" / "sample"
DB_PATH = ROOT / "db" / "market.db"
OUT_DIR = ROOT / "outputs"
CHART_DIR = OUT_DIR / "charts"
REPORT_DIR = ROOT / "reports"

DEFAULT_TICKER = "DEMO_AAPL"
DEMO_TICKERS = ("DEMO_AAPL", "DEMO_NVDA", "DEMO_RELIANCE")
TRADING_DAYS = 252  # Standard approximation for annualizing daily metrics


def ensure_dirs():
    for folder in (SAMPLE_DIR, DB_PATH.parent, OUT_DIR, CHART_DIR, REPORT_DIR):
        folder.mkdir(parents=True, exist_ok=True)
