# Stock Market Data Analyzer — DEMO_AAPL

**Data source:** SAMPLE  
**Period:** 2024-01-02 to 2026-11-20  
**Observations:** 754 daily trading rows

> SYNTHETIC DEMONSTRATION DATA. Not real stock prices.

## Price and trend analysis

| Measure | Result |
|---|---:|
| First adjusted closing price | 140.05 |
| Latest adjusted closing price | 64.60 |
| Adjusted price change | -53.87% |
| Highest raw trading high | 141.11 |
| Lowest raw trading low | 50.53 |
| Daily average adjusted return | -0.094% |
| Annualized historical volatility | 20.90% |
| SMA 20 | 62.16 |
| SMA 50 | 64.00 |
| RSI 14 | 59.00 |

**Latest trend observation:** Above SMA20 & SMA50.  
**Latest SMA crossover event in history:** CROSS_DOWN (not necessarily today).

## Educational SMA 20/50 strategy backtest

| Measure | Result |
|---|---:|
| Backtest period | 2024-03-11 to 2026-11-20 |
| Simulated strategy return | -39.28% |
| Simulated buy-and-hold return | -45.88% |
| Maximum drawdown | -40.20% |
| Annualized Sharpe (0% risk-free assumption) | -1.42 |
| Entries | 8 |
| Completed trades | 8 |
| Win rate of completed trades | 12.50% |
| Fee assumption | 5.0 bps per position change |
| Slippage assumption | 2.0 bps per position change |

## How to interpret

- The 20-day and 50-day simple moving averages reduce day-to-day price noise.
- Return is calculated from adjusted close where available. Raw OHLC high/low are shown separately.
- Volatility is the sample standard deviation of daily adjusted returns multiplied by √252.
- A crossover is a mechanical observation, **not** a suggestion to buy or sell.
- Strategy signals use prior day's information (`shift(1)`) to avoid same-bar look-ahead.

## Limitations and disclaimer

Simplified close-to-close simulation, delayed signal, no taxes/market impact. Educational only. Adjusted prices are not executable trade prices. No tax, liquidity,
spread changes, survivorship bias, corporate action modeling, market impact or actual orders.
Free Yahoo data may have delays, download failures, or licensing restrictions.
**This project is for education only. It is not financial advice.**
