# Interview preparation — Stock Market Data Analyzer

## HR: 30-second explanation

"I built a Python-based market data analyzer that reads free historical data or synthetic CSV files, cleans the data, calculates returns and indicators, and produces charts and a written report. I also implemented a simple rule-based historical backtest, SQLite storage, an optional API and dashboard, and tests. This project taught me data pipelines, exploratory analysis, time-series calculations and how to communicate risks and limitations. The tool is educational and does not execute trades."

## Technical: 60-second explanation

"The app's ingestion module accepts OHLCV bars from Yahoo Finance, CSV or reproducible synthetic data. A validation stage standardizes timestamps and columns and rejects missing or invalid OHLC rows. Pandas computes adjusted-close returns, SMA20/SMA50, RSI14, MACD, Bollinger Bands and annualized volatility. I save candles and indicators with ticker/date keys in SQLite and generate Matplotlib charts and a Markdown/JSON report. A long-only crossover backtest applies each day's signal to the *next* day's return, charges configurable fees and slippage, and calculates total return, maximum drawdown and Sharpe ratio. FastAPI exposes endpoint data; Streamlit and optional Next.js show trends, watchlists, paper transactions and manual threshold alerts. The included offline tests check pipeline behavior and REST endpoints."

## 10 important questions with strong answers

**1. Explain your project.**

It is a historical stock-price research application built with Python. It loads demo CSV or Yahoo history, cleans OHLCV bars, computes returns and technical indicators, generates charts/reports, and tests a basic strategy without placing real trades. It also has a dashboard and REST API.

**2. What problem does this solve?**

It automates repeated spreadsheet work and makes a price analysis reproducible. A user can compare trends, risk metrics and strategy assumptions with the same process for each symbol.

**3. Which tools did you use?**

Python for orchestration; Pandas/NumPy for time-series math; Matplotlib and Plotly for charts; yfinance for public historical prices; SQLite for persistent records; Streamlit and Next.js for user interfaces; FastAPI for endpoints; pytest for tests.

**4. What data did you analyze?**

Daily open, high, low, close, adjusted close, volume and date. Returns and moving averages rely on adjusted close where available. The included `DEMO_` CSV data are synthetic, not actual securities prices.

**5. What are moving averages and what do they show?**

SMA20 is the arithmetic mean of the last 20 daily adjusted closes, and SMA50 uses 50. They smooth noise. Crossovers may identify historical trend changes but cannot predict the next price reliably.

**6. What is daily return?**

`(AdjustedClose_today / AdjustedClose_previous_day) - 1`. It measures period-to-period percentage change, including adjusted corporate actions where the provider adjustment is correct.

**7. What is volatility?**

Standard deviation of daily returns, usually annualized by multiplying by `sqrt(252)` for daily stock trading data. It measures historical fluctuations, not all possible investment risks.

**8. What files does the project produce?**

An analyzed CSV; three actual PNG charts showing price, SMA and return distribution; a Markdown summary report; a JSON metrics report; plus SQLite data used by the API and dashboard.

**9. What technical challenges did you face?**

Different Yahoo column structures, insufficient price history, invalid duplicate rows, avoiding forward-filled prices, avoiding look-ahead in backtests, counting trades correctly, and storing portfolio cost basis accurately. I separated modules and tested these behaviors offline.

**10. How do you explain it to someone without a finance background?**

Imagine a calculator that takes a record of daily prices, makes pictures of how those prices changed, tells you how much they bounced up and down, and compares a pretend trading rule with simply holding. It shows historical patterns and does not tell you what to buy.

## Two follow-up questions interviewers may ask

**Q: Why `shift(1)` in the backtest?**

A signal calculated using today's close cannot be used to earn today's earlier price movement. Shifting the position forces the trade rule to act on the next period, avoiding one common form of look-ahead bias.

**Q: Is yfinance truly real-time and is your strategy profitable?**

No. Yahoo access and update frequency vary; prices can be delayed or unavailable. This is a historical educational system, and a positive backtest (if present) would not demonstrate future profitability. The included default sample is synthetic.
