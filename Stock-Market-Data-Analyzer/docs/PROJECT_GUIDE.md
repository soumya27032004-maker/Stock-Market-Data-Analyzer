# Complete beginner project guide — Stock Market Data Analyzer

## 1. Explanation

### Very simple explanation
Imagine a school notebook with a company's stock prices on different days. Instead of manually adding every number, this Python application reads the notebook (CSV or Yahoo Finance historical data), finds changes, calculates trends and risk, draws graphs, and writes a short report. It **does not know** whether tomorrow's price will rise.

### Technical explanation
An ETL/time-series analytics pipeline collects daily OHLCV bars, checks date/price validity, calculates price-based indicators on adjusted close, stores results in SQLite, backtests a delayed-signal strategy with approximate costs, and exposes data via FastAPI. Streamlit is the easiest Python-only front end. An optional Next.js + Recharts client consumes the same API. Paper positions and alert conditions are stored locally.

### Problem / usefulness
Investors and finance analysts often need reproducible research without manually preparing spreadsheets. Python reduces repetitive calculations, improves traceability, permits sensitivity tests and makes charts easy to compare. In industry, similar patterns are used for watchlists, historical research, risk monitoring, strategy prototyping and education; professionals additionally require licensed real-time data, robust compliance, corporate-action handling and risk controls.

### Complete workflow

```text
Ticker / Date Range / Local CSV
            |
            v
  Yahoo download OR offline synthetic CSV
            |
            v
   Validate OHLCV + remove bad/duplicate rows
            |
            v
   Adjusted close → Returns / SMA / RSI / MACD / Bollinger / Volatility
            |
            +--> Charts PNG & analysis CSV
            |
            +--> SQLite tables (candles, indicators, symbols)
            |        |
            |        +--> FastAPI → Next.js dashboard
            |        +--> Watchlist, paper portfolio & alert rules
            |
            +--> Shifted SMA backtest + transaction cost estimates
                     |
                     v
            Report Markdown + JSON
```

**OHLCV** = Open, High, Low, Close and Volume. **Adjusted close** attempts to account for corporate actions; it is not the actual price at which you execute an order. Synthetic files use fake prices and have no splits/dividends.

## 2. Three possible technology stacks

| Option | Tools | Difficulty | Expected output |
|---|---|---|---|
| A: Easy | Python, Pandas, NumPy, Matplotlib, sample CSV | Beginner | CSV, simple charts, summary |
| **B: Intermediate (best student choice)** | Above + yfinance, Streamlit, SQLite, pytest | Beginner–intermediate | Interactive dashboard, historical metrics, reports, backtest |
| C: Advanced (included as an optional extension) | FastAPI, Next.js, Recharts, local alert storage | Intermediate–advanced | API endpoints, React interface, watchlist, paper portfolio |

**Recommended order:** Run the easy offline pipeline first, use Streamlit second, and open the FastAPI/Next.js UI only after you are comfortable. All source code is included, but the Next.js UI is optional and needs Node.js.

## 3. Project architecture and folder structure

| Path | Purpose |
|---|---|
| `main.py` | One-command data analysis and file creation |
| `src/data.py` | Yahoo/CSV/demo loaders and cleaning |
| `src/indicators.py` | Returns, SMA, RSI, MACD, Bollinger, volatility |
| `src/backtest.py` | Long-only SMA strategy simulator with delayed signals |
| `src/store.py` | SQLite, watchlist, alerts and weighted-average portfolio ledger |
| `src/viz.py` | Three PNG charts |
| `src/report.py` | Markdown and JSON reports |
| `dashboard.py` | Beginner Streamlit interface |
| `api/app.py` | REST API with documentation at `/docs` |
| `apps/web/` | Optional Next.js dashboard |
| `db/schema.sql` | Database table definitions |
| `data/sample/` | **Synthetic** practice stock data |
| `data/imports/` | Put your own CSV here; ignored by Git |
| `outputs/` | Analysis CSV and charts |
| `reports/` | Written reports |
| `images/` | Capture your own dashboard/terminal screenshots here |
| `notebooks/` | Space for future Jupyter work |
| `tests/` | Offline automated unit + API tests |
| `.github/workflows/test.yml` | CI workflow that runs tests after a GitHub push |
| `docs/` | Setup, project walkthrough, GitHub, interview prep |
| `requirements.txt` | Python libraries |
| `.gitignore` | Excludes secrets, environment and local DB |

## 4. Ten-phase implementation plan: what / why / output / mistakes

| Phase | What to do | Why | Output | Common mistake |
|---|---|---|---|---|
| 1 Setup | Install Python and dependencies | Run code | `.venv` and packages | Not enabling PATH / running inside ZIP |
| 2 Folder | Extract files and open the project root | Correct relative paths | `main.py`, `src/` | Running from another directory |
| 3 Collect | Load demo, Yahoo history or CSV | Get prices | DataFrame of OHLCV | Using wrong exchange suffix |
| 4 Clean | Convert dates, numeric columns, remove invalid rows | Reliable measurements | Clean daily table | Forward-filling fake prices |
| 5 EDA | Check ranges, highs and lows | Understand price history | Price summary | Confusing high with adjusted close |
| 6 MA | Calculate rolling SMA20 and SMA50 | Trend observation | SMA columns | Treating SMA as a forecast |
| 7 Risk | Calculate returns and annualized volatility | Compare historical fluctuations | Daily returns, vol | Treating past vol as future certainty |
| 8 Visualize | Draw line and histogram charts | See trends/distribution | Three PNGs | Forgetting titles and axis units |
| 9 Report | Produce written summary and backtest | Communicate results | `.md`, `.json`, `.csv` | Claiming performance is guaranteed |
| 10 GitHub | Test, document and push source | Show independent proof | Portfolio repository | Uploading `.venv` or personal API keys |

## 5. How to run

### First launch, Windows

Read `START_HERE.txt`. Double-click `start_windows.bat`; it installs packages inside the project's `.venv` and runs `DEMO_AAPL` using offline CSV. Double-click `dashboard_windows.bat` for the Streamlit dashboard.

### CLI (Windows Command Prompt)

```bat
cd path\to\Stock-Market-Data-Analyzer
py -3 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe main.py
.venv\Scripts\python.exe -m streamlit run dashboard.py
```

### CLI (macOS/Linux Terminal)

```bash
cd path/to/Stock-Market-Data-Analyzer
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python main.py
streamlit run dashboard.py
```

### Run with a real ticker (public Yahoo historical data)

```bash
python main.py --source yahoo --ticker AAPL --start 2024-01-01
python main.py --source yahoo --ticker RELIANCE.NS --start 2024-01-01
```

Yahoo may reject requests, be offline, have missing bars or have delayed data. No paid terminal is necessary, but this is **not a guaranteed live feed**. The end date in yfinance is exclusive.

### Run with your own CSV

CSV needs columns `Date,Open,High,Low,Close,Volume`. `Adj Close` is optional. To use your own data:

```bash
python main.py --source csv --ticker MY_STOCK --file data/imports/my_prices.csv
```

The project does not fabricate missing data, and it requires at least 55 valid daily observations for indicator analysis. CSV data may have different dates or currencies; identify its exchange/currency outside this tool.

### Run tests

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

## 6. Optional advanced API + Next.js dashboard

In Terminal 1, **inside the root project folder**:

```bash
python -m uvicorn api.app:app --host 127.0.0.1 --port 8000
```

Open <http://127.0.0.1:8000/docs> and test `GET /health`, `GET /chart/DEMO_AAPL`, `POST /backtest/sma`. The API loads all three demo symbols on startup if missing. It does not fetch data continually.

In Terminal 2, install **Node.js 20.9+** and run:

```bash
cd apps/web
npm install
npm run dev
```

Open <http://127.0.0.1:3000>. The Next.js app uses an internal URL rewrite `/api/*` → `http://127.0.0.1:8000/*`. Keep both terminals open. Never expose the API to the internet without authentication, CORS/security review and rate limiting.

### API endpoint overview

- `GET /health` — health status
- `POST /refresh/{ticker}` — download Yahoo history or load demo data, and save in SQLite
- `GET /chart/{ticker}?days=252` — historical OHLC + indicators
- `GET /summary/{ticker}` — trend/volatility summary
- `POST /backtest/sma` — historical SMA crossover simulation
- `GET /watchlist`, `POST /watchlist`, `DELETE /watchlist/{ticker}` — manage local symbols
- `GET /portfolio/positions`, `GET/POST /portfolio/transactions` — paper trades only
- `GET/POST /alerts`, `POST /alerts/check`, `GET /alerts/events` — manual local alert checks

## 7. Virtual simulation: what happens in the demo

1. `data/sample/DEMO_AAPL.csv` contains **754 artificially generated business-day rows** from January 2, 2024 through November 20, 2026. They are not real Apple quotes.
2. Data loader validates prices, dates and volume, dropping corrupted rows; SQLite stores the resulting bars.
3. `pct_change()` calculates day-over-day adjusted price returns.
4. `rolling(20)` / `rolling(50)` show smoothed price trends; an SMA crossover is a **rule**, not advice.
5. Annualized historical volatility = `std(daily returns) × sqrt(252)`.
6. The simulation tests a long-only strategy: when SMA20 is above SMA50 at day *t*, exposure applies to day *t+1*; fees/slippage apply when exposure changes.
7. Matplotlib saves three charts; `reports/` receives a markdown report and JSON summary.
8. The Streamlit and Next.js dashboards display history, a paper portfolio, watchlist, and alerts.

**Metrics have important assumptions:** Sharpe assumes a 0% risk-free rate; backtest execution is close-to-close approximate. No tax, spread variation, borrow, bid/ask or market-impact model. Win rate counts *completed* simulated trades only. The annualization convention of 252 trading days is approximate. This is not validated for live trading.

## 8. Exactly what to screenshot

1. Project folder showing `main.py`, `src`, `reports` and `outputs`.
2. Excel/CSV viewer showing `DEMO_AAPL` rows, clearly marked synthetic.
3. Command Prompt showing `SUCCESS | DEMO_AAPL`.
4. The saved `DEMO_AAPL_price.png` file (actual generated chart).
5. The saved `DEMO_AAPL_moving_averages.png` file.
6. The saved `DEMO_AAPL_daily_returns.png` file.
7. Streamlit screen with annualized volatility and the backtest results.
8. `reports/DEMO_AAPL_report.md` open in a text/Markdown viewer.
9. FastAPI `/docs` with routes visible.
10. Your public GitHub repo home page, showing `README.md` and screenshots.

Save your personal screenshots as `images/01_project_folder.png`, etc. See `images/SCREENSHOT_CHECKLIST.md`. Only include screenshots of outputs you actually ran; the repository's generated charts are authentic offline demo artifacts.

## 9. Build proof on GitHub over six days

| Day | Work | Suggested commit | Screenshot |
|---|---|---|---|
| 1 | Set up Python and project | `Set up Python environment and project folders` | Folder / installed packages |
| 2 | Load sample and Yahoo data | `Implement OHLCV ingestion and CSV fallback` | Dataset |
| 3 | Add cleaning and exploratory analysis | `Validate stock data and add summary metrics` | Terminal summary |
| 4 | Add MAs, RSI, volatility and backtest | `Add technical indicators and delayed SMA backtest` | Charts / metrics |
| 5 | Add Matplotlib and Streamlit UI | `Visualize prices risk and backtests` | Dashboard |
| 6 | Add tests, reports and READMEs | `Document and test analyzer for portfolio` | Report / GitHub home |

You already have the completed starter source in this archive. To demonstrate your own contribution, re-run, improve, and commit meaningful changes rather than pretending you wrote all the code yourself.

## 10. Future industry-focused upgrades

- Licensed streaming data or exchange feeds with clear timestamp/time-zone handling.
- Per-symbol currency/market calendars, split/dividend audit and time-zone normalization.
- Transaction cost and bid/ask spread models using plausible execution prices.
- Risk-aware portfolio monitoring and trade-level reconciliation.
- Walk-forward validation, benchmark selection and realistic out-of-sample evaluation.
- API authorization, credential management, background jobs and optional notification services.
- Audit logs, data-source caching and streaming status.

## 11. Final warnings

This is **educational software**. No real-money order is sent, no returns are promised, and alerts are local/manual only. Never confuse synthetic `DEMO_` data with market quotes. Historical information is not a forecast or personalized financial advice.
