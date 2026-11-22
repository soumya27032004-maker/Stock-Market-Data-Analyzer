"""Beginner entry point. This runs OFFLINE by default.

Examples:
  python main.py
  python main.py --source yahoo --ticker AAPL --start 2023-01-01
  python main.py --source yahoo --ticker RELIANCE.NS --start 2023-01-01
  python main.py --source csv --file data/imports/my_prices.csv --ticker MY_STOCK
"""
import argparse
import json
from src.config import CHART_DIR, DB_PATH, OUT_DIR, REPORT_DIR, DEFAULT_TICKER, ROOT, ensure_dirs
from src.data import get_prices, ticker_valid
from src.indicators import compute_indicators, summarize
from src.backtest import run_sma_backtest
from src.report import write_report
from src.store import add_watchlist, save_analysis, save_backtest
from src.viz import create_charts


def run(source="sample", ticker=DEFAULT_TICKER, start="2024-01-01", end=None, file=None,
        fee_bps=5.0, slippage_bps=2.0, db_path=DB_PATH):
    ensure_dirs()
    ticker = ticker_valid(ticker)
    prices = get_prices(source, ticker, start, end, file)
    analysis = compute_indicators(prices)
    summary = summarize(analysis, ticker, source)
    stats = run_sma_backtest(analysis, fee_bps, slippage_bps)
    save_analysis(ticker, source, analysis, db_path)
    save_backtest(ticker, stats, {"fee_bps": fee_bps, "slippage_bps": slippage_bps}, db_path)
    add_watchlist(ticker, db_path)
    csv_path = OUT_DIR / f"{ticker}_analysis.csv"
    analysis.to_csv(csv_path, index=False, float_format="%.7f")
    images = create_charts(analysis, ticker, CHART_DIR)
    report_path = write_report(summary, stats, REPORT_DIR)
    print(f"\nSUCCESS | {ticker} | {source} | {summary['rows']} rows")
    print(f"Dates: {summary['first_date']} to {summary['last_date']}")
    print(f"Price change: {summary['price_change_pct']:.2f}%")
    print(f"Annualized volatility: {summary['annual_volatility_pct']:.2f}%")
    print(f"Backtest return: {stats['total_return'] * 100:.2f}% | Buy & hold: {stats['buy_hold_return'] * 100:.2f}%")
    print(f"Analysis CSV: {csv_path.relative_to(ROOT)}")
    print(f"Report: {report_path.relative_to(ROOT)}")
    for chart in images:
        print(f"Chart: {chart.relative_to(ROOT)}")
    print("DISCLAIMER: Synthetic data in sample mode; not financial advice.")
    return {"summary": summary, "stats": stats, "csv": str(csv_path), "report": str(report_path)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Historical Stock Market Data Analyzer")
    parser.add_argument("--source", choices=["sample", "csv", "yahoo"], default="sample")
    parser.add_argument("--ticker", default=DEFAULT_TICKER)
    parser.add_argument("--start", default="2024-01-01")
    parser.add_argument("--end", default=None, help="Yahoo end date is EXCLUSIVE")
    parser.add_argument("--file", default=None)
    parser.add_argument("--fee-bps", type=float, default=5)
    parser.add_argument("--slippage-bps", type=float, default=2)
    args = parser.parse_args()
    try:
        run(**vars(args))
    except (ValueError, FileNotFoundError, RuntimeError, OSError) as error:
        parser.exit(1, f"ERROR: {error}\nSee START_HERE.txt for help.\n")
