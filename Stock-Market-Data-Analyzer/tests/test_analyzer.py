"""Network-free tests. Run: python -m pytest -q"""
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient
from src.config import SAMPLE_DIR
from src.data import from_csv, get_prices, clean_prices
from src.indicators import compute_indicators, summarize
from src.backtest import run_sma_backtest
from src import store
from api.app import create_app


def test_cleaning_removes_invalid_and_duplicate_rows():
    raw = get_prices("sample", "DEMO_AAPL")
    bad = raw.iloc[0].copy()
    bad["high"] = 0.001
    copy = pd.concat([raw.iloc[::-1], pd.DataFrame([bad])], ignore_index=True)
    assert len(clean_prices(copy)) == len(raw)
    with pytest.raises(ValueError, match="missing required"):
        clean_prices(pd.DataFrame({"Date": ["2024-01-02"]}))


def test_demo_data_is_reproducible_and_technical_metrics():
    frame = get_prices("sample", "DEMO_AAPL")
    assert len(frame) > 500
    assert frame["adj_close"].equals(frame["close"])
    df = compute_indicators(frame)
    assert pd.isna(df.loc[18, "sma20"])
    assert pd.notna(df.loc[19, "sma20"])
    assert pd.isna(df.loc[48, "sma50"])
    assert pd.notna(df.loc[49, "sma50"])
    assert df["rsi14"].dropna().between(0, 100).all()
    s = summarize(df, "DEMO_AAPL", "sample")
    assert s["rows"] == len(frame)
    assert s["annual_volatility_pct"] > 0


def test_shifted_backtest_matches_previous_signal_and_fees():
    frame = compute_indicators(get_prices("sample", "DEMO_NVDA"))
    bt = run_sma_backtest(frame, fee_bps=6, slippage_bps=3)
    d = frame.dropna(subset=["sma20", "sma50"]).reset_index(drop=True)
    desired = (d["sma20"] > d["sma50"]).astype(int)
    position = desired.shift(1).fillna(0).astype(int)
    turnover = position.diff().fillna(position.iloc[0]).abs()
    ret = d["adj_close"].pct_change().fillna(0)
    expected = (1 + position * ret - turnover * .0009).cumprod().iloc[-1] - 1
    assert np.isclose(bt["total_return"], expected)
    assert bt["first_date"] == d["date"].iloc[0]
    assert bt["max_drawdown"] <= 0
    assert bt["trades"] >= 0
    assert len(bt["curve"]) == len(d)
    assert bt["closed_trades"] <= bt["trades"]
    with pytest.raises(ValueError):
        run_sma_backtest(frame, -1)


def test_store_portfolio_and_alert_de_duplication(tmp_path):
    db = tmp_path / "test.db"
    store.init_db(db)
    data = compute_indicators(get_prices("sample", "DEMO_RELIANCE"))
    store.save_analysis("DEMO_RELIANCE", "sample", data, db)
    assert len(store.list_chart("DEMO_RELIANCE", path=db)) == 252
    store.add_transaction("DEMO_RELIANCE", "BUY", 4, 100, 2, path=db)
    store.add_transaction("DEMO_RELIANCE", "BUY", 6, 200, 0, path=db)
    result = store.positions(db)[0]
    assert result["quantity"] == 10
    assert np.isclose(result["average_cost"], 160.2)
    with pytest.raises(ValueError, match="Cannot sell"):
        store.add_transaction("DEMO_RELIANCE", "SELL", 12, 100, path=db)
    store.add_transaction("DEMO_RELIANCE", "SELL", 5, 220, 1, path=db)
    result = store.positions(db)[0]
    assert result["quantity"] == 5
    assert np.isclose(result["realized_pnl"], 5 * (220-160.2)-1)
    store.add_alert("DEMO_RELIANCE", "CLOSE_ABOVE", 0.01, path=db)
    assert len(store.check_alerts(db)) == 1
    assert len(store.check_alerts(db)) == 0
    assert len(store.alert_events(db)) == 1


def test_api_sample_bootstrap_and_routes(tmp_path):
    app = create_app(tmp_path / "api.db")
    with TestClient(app) as client:
        assert client.get("/health").json()["ok"] is True
        rows = client.get("/chart/DEMO_AAPL", params={"days": 50})
        assert rows.status_code == 200 and len(rows.json()) == 50
        assert len(client.get("/watchlist").json()) >= 3
        r = client.post("/backtest/sma", json={"ticker": "DEMO_AAPL"})
        assert r.status_code == 200
        assert "total_return" in r.json()["stats"]
        t = client.post("/portfolio/transactions", json={"ticker":"DEMO_AAPL","side":"BUY","qty":2,"price":130})
        assert t.status_code == 200
        assert client.get("/portfolio/positions").json()[0]["quantity"] == 2
        bad = client.post("/portfolio/transactions",json={"ticker":"DEMO_AAPL","side":"SELL","qty":9,"price":130})
        assert bad.status_code == 400
        assert client.post("/alerts",json={"ticker":"DEMO_AAPL","rule":"RSI_BELOW","threshold":90}).status_code == 200
        assert client.post("/alerts/check").status_code == 200
        assert client.post("/refresh/DEMO_AAPL",json={"source":"sample"}).json()["ok"] is True


def test_csv_input_from_example(tmp_path):
    f = tmp_path / "custom.csv"
    sample = get_prices("sample", "DEMO_AAPL").rename(columns={"date": "Date", "adj_close": "Adj Close"})
    sample.to_csv(f, index=False)
    assert len(from_csv(f)) == len(sample)
