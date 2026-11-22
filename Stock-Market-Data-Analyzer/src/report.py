"""Write plain-language reports with explicit assumptions and sourcing."""
import json
from pathlib import Path


def write_report(summary: dict, backtest: dict, report_dir: Path):
    report_dir.mkdir(parents=True, exist_ok=True)
    ticker = summary["ticker"]
    def fmt(key, suf="", digits=2):
        val = summary.get(key)
        return "N/A" if val is None else f"{val:,.{digits}f}{suf}"
    def bt_fmt(key, percentage=False):
        val = backtest.get(key)
        if val is None:
            return "N/A"
        return f"{val * 100:.2f}%" if percentage else f"{val:.2f}"
    markdown = f"""# Stock Market Data Analyzer — {ticker}

**Data source:** {summary['source'].upper()}  
**Period:** {summary['first_date']} to {summary['last_date']}  
**Observations:** {summary['rows']} daily trading rows

> {'SYNTHETIC DEMONSTRATION DATA. Not real stock prices.' if summary['source'] == 'sample' else 'Historical data; may be delayed, incomplete or revised.'}

## Price and trend analysis

| Measure | Result |
|---|---:|
| First adjusted closing price | {fmt('first_adj_close')} |
| Latest adjusted closing price | {fmt('last_adj_close')} |
| Adjusted price change | {fmt('price_change_pct', '%')} |
| Highest raw trading high | {fmt('highest_raw_high')} |
| Lowest raw trading low | {fmt('lowest_raw_low')} |
| Daily average adjusted return | {fmt('daily_avg_return_pct', '%', 3)} |
| Annualized historical volatility | {fmt('annual_volatility_pct', '%')} |
| SMA 20 | {fmt('sma20')} |
| SMA 50 | {fmt('sma50')} |
| RSI 14 | {fmt('rsi14')} |

**Latest trend observation:** {summary['trend_observation']}.  
**Latest SMA crossover event in history:** {summary['latest_crossover']} (not necessarily today).

## Educational SMA 20/50 strategy backtest

| Measure | Result |
|---|---:|
| Backtest period | {backtest['first_date']} to {backtest['last_date']} |
| Simulated strategy return | {bt_fmt('total_return', True)} |
| Simulated buy-and-hold return | {bt_fmt('buy_hold_return', True)} |
| Maximum drawdown | {bt_fmt('max_drawdown', True)} |
| Annualized Sharpe (0% risk-free assumption) | {bt_fmt('sharpe')} |
| Entries | {backtest['trades']} |
| Completed trades | {backtest['closed_trades']} |
| Win rate of completed trades | {bt_fmt('win_rate', True)} |
| Fee assumption | {backtest['fee_bps']} bps per position change |
| Slippage assumption | {backtest['slippage_bps']} bps per position change |

## How to interpret

- The 20-day and 50-day simple moving averages reduce day-to-day price noise.
- Return is calculated from adjusted close where available. Raw OHLC high/low are shown separately.
- Volatility is the sample standard deviation of daily adjusted returns multiplied by √252.
- A crossover is a mechanical observation, **not** a suggestion to buy or sell.
- Strategy signals use prior day's information (`shift(1)`) to avoid same-bar look-ahead.

## Limitations and disclaimer

{backtest['note']} Adjusted prices are not executable trade prices. No tax, liquidity,
spread changes, survivorship bias, corporate action modeling, market impact or actual orders.
Free Yahoo data may have delays, download failures, or licensing restrictions.
**This project is for education only. It is not financial advice.**
"""
    (report_dir / f"{ticker}_report.md").write_text(markdown, encoding="utf-8")
    (report_dir / f"{ticker}_summary.json").write_text(
        json.dumps({"summary": summary, "backtest": {k: v for k, v in backtest.items() if k != "curve"}},
                   indent=2, ensure_ascii=False), encoding="utf-8")
    return report_dir / f"{ticker}_report.md"
