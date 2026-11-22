# Upload this project to GitHub (very easy)

## Option 1 — Use the GitHub website (no Git commands)

1. Go to <https://github.com/> and sign in (or make a free account).
2. On the top right, click **+** and select **New repository**.
3. Repository name: **Stock-Market-Data-Analyzer**.
4. Description: **Python stock data analysis with technical indicators, visualizations, strategy backtesting, FastAPI and dashboards.**
5. Choose **Public** for your student portfolio. Leave the **Initialize with README** box unchecked if you will upload the existing README.
6. Click **Create repository**.
7. Click **uploading an existing file**.
8. Open your extracted `Stock-Market-Data-Analyzer` folder in Windows File Explorer.
9. Select project files and folders and drag them onto the GitHub upload area. **Do not upload** `.venv`, `db/market.db`, or `apps/web/node_modules`. The website may limit large/many-file uploads; use GitHub Desktop or Git if needed.
10. In **Commit changes**, type `Initial commit: stock analyzer with sample results` and click **Commit changes**.
11. On your new repository, open `README.md`. Charts should appear, and code folders should be visible.
12. Add these topics in the repository **About** panel: `python`, `pandas`, `stock-market`, `data-analysis`, `fintech`, `fastapi`, `nextjs`, `streamlit`, `backtesting`.

> **Nested files and empty folders:** Web uploads can be awkward for deeply nested projects. For an entire repository with correct folders, **GitHub Desktop** or Option 2 is usually more reliable.

## Option 2 — Git commands (recommended when you learn Git)

Open a terminal **inside the extracted project folder** (click File Explorer's address bar, type `cmd`, press Enter):

```bash
git init
git add .
git commit -m "Initial working stock data analyzer"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/Stock-Market-Data-Analyzer.git
git push -u origin main
```

Replace **YOUR-USERNAME** with your own GitHub username. Create a blank GitHub repository first. Git must be installed from <https://git-scm.com/>. When GitHub requests authentication, follow its browser login or personal-access-token instructions; **never publish passwords, tokens, or API keys**.

For future improvements:

```bash
git add .
git commit -m "Add watchlist and backtest improvements"
git push
```

## Before uploading: proof-of-work checklist

- [ ] `python main.py` prints **SUCCESS**.
- [ ] `python -m pytest -q` passes (requires `requirements-dev.txt`).
- [ ] `outputs/charts/` contains real screenshots of generated charts.
- [ ] `reports/DEMO_AAPL_report.md` contains the analysis.
- [ ] `images/` contains your own terminal/dashboard screenshots if you captured them.
- [ ] `.venv/` and all personal keys are excluded.
- [ ] GitHub README explains synthetic DEMO data and what is/not financial advice.

## Suggested repository and GitHub text

**Name:** `Stock-Market-Data-Analyzer`

**Short description:** `End-to-end Python market data analysis: CSV/Yahoo data, SMA/RSI/MACD, risk metrics, charts, SQLite, FastAPI, Next.js and paper portfolio.`

**Topics:** `python`, `finance`, `pandas`, `yfinance`, `technical-analysis`, `fastapi`, `streamlit`, `nextjs`, `portfolio`, `data-visualization`.

**Profile proof:** Put the repository link in the Projects section of your résumé, mention the tested offline sample, and explain that it is a research tool rather than a live-trading tool.
