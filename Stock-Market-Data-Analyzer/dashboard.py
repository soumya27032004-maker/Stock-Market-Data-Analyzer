"""Streamlit UI. Run from project root: streamlit run dashboard.py"""
from datetime import date
from io import BytesIO
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from src.config import DEFAULT_TICKER, DEMO_TICKERS, DB_PATH
from src.data import clean_prices, get_prices, ticker_valid
from src.indicators import compute_indicators, summarize
from src.backtest import run_sma_backtest
from src import store

st.set_page_config(page_title="Stock Market Data Analyzer", page_icon="📈", layout="wide")
st.title("📈 Stock Market Data Analyzer")
st.caption("Student project • Historical/delayed Yahoo data or synthetic demo • Never live trading")
st.warning("For learning only. Not financial advice. Demo prices are synthetic and not real quotes.", icon="ℹ️")
store.init_db(DB_PATH)

with st.sidebar:
    st.header("1. Choose data")
    source_label = st.radio("Data source", ["Sample (works offline)", "Yahoo Finance", "Upload CSV"])
    source = {"Sample (works offline)": "sample", "Yahoo Finance": "yahoo", "Upload CSV": "csv"}[source_label]
    if source == "sample":
        ticker = st.selectbox("Demo ticker", DEMO_TICKERS)
    else:
        ticker = st.text_input("Ticker", "RELIANCE.NS" if source == "yahoo" else "MY_STOCK")
    start = st.date_input("Start date (Yahoo only)", value=date(2024, 1, 1))
    upload = st.file_uploader("CSV with Date,Open,High,Low,Close,Volume", type=["csv"]) if source == "csv" else None
    st.caption("Indian examples: RELIANCE.NS, TCS.NS; US example: AAPL")
    load = st.button("2. Load & analyze", type="primary", use_container_width=True)

if load:
    try:
        cleaned_ticker = ticker_valid(ticker)
        if source == "csv":
            if upload is None:
                raise ValueError("Select a CSV file first.")
            df = clean_prices(pd.read_csv(BytesIO(upload.getvalue())))
        else:
            df = get_prices(source, cleaned_ticker, start.isoformat())
        analysis = compute_indicators(df)
        store.save_analysis(cleaned_ticker, source, analysis, DB_PATH)
        store.add_watchlist(cleaned_ticker, DB_PATH)
        st.session_state["analysis"] = analysis
        st.session_state["ticker"] = cleaned_ticker
        st.session_state["source"] = source
        st.session_state.pop("backtest", None)  # never show a prior ticker's results
        st.success(f"Loaded {len(df)} rows for {cleaned_ticker}.")
    except Exception as exc:
        st.error(str(exc))

if "analysis" not in st.session_state:
    frame = compute_indicators(get_prices("sample", DEFAULT_TICKER))
    store.save_analysis(DEFAULT_TICKER, "sample", frame, DB_PATH)
    st.session_state.update(analysis=frame, ticker=DEFAULT_TICKER, source="sample")

df = st.session_state["analysis"]
symbol = st.session_state["ticker"]
origin = st.session_state["source"]
info = summarize(df, symbol, origin)

analysis_tab, backtest_tab, watch_tab, portfolio_tab, alerts_tab = st.tabs(
    ["Overview & charts", "Backtest", "Watchlist", "Portfolio (paper)", "Alerts (local)"])
with analysis_tab:
    a,b,c,d = st.columns(4)
    a.metric("Last adjusted close", f"{info['last_adj_close']:,.2f}")
    b.metric("Period adjusted return", f"{info['price_change_pct']:.2f}%")
    c.metric("Annualized volatility", f"{info['annual_volatility_pct']:.2f}%")
    d.metric("RSI 14", f"{info['rsi14']:.1f}" if info['rsi14'] is not None else "N/A")
    st.caption(f"{symbol} · {info['first_date']} → {info['last_date']} · {len(df)} trading days · {info['trend_observation']}")
    p = go.Figure()
    for label, key in [("Adj close", "adj_close"), ("SMA 20", "sma20"), ("SMA 50", "sma50")]:
        p.add_trace(go.Scatter(x=df["date"], y=df[key], name=label, mode="lines"))
    p.update_layout(title="Adjusted price and simple moving averages", xaxis_title="Date",
                    yaxis_title="Price (original ticker currency / demo units)", height=430,
                    margin=dict(l=20,r=20,t=55,b=15))
    st.plotly_chart(p, use_container_width=True)
    left,right = st.columns(2)
    with left:
        st.subheader("Daily adjusted returns")
        st.bar_chart(df.set_index("date")["daily_return"] * 100, y_label="Return (%)")
    with right:
        st.subheader("Historical rolling annualized volatility")
        st.line_chart(df.set_index("date")["rolling_vol20"] * 100, y_label="Volatility (%)")
    st.subheader("Technical indicators")
    st.dataframe(df[["date", "adj_close", "sma20", "sma50", "rsi14", "macd", "signal"]].tail(15),
                 hide_index=True, use_container_width=True)
    st.download_button("Download analysis CSV", df.to_csv(index=False).encode(),
                       file_name=f"{symbol}_analysis.csv", mime="text/csv")

with backtest_tab:
    st.subheader("Long-only SMA20/50 crossover (historical simulation)")
    st.caption("Yesterday's signal controls today's exposure. Fee and slippage charged on position changes.")
    fee, slip = st.columns(2)
    fee_bps = fee.number_input("Fee (basis points per trade)", min_value=0.0, max_value=1000.0, value=5.0)
    slip_bps = slip.number_input("Slippage (basis points per trade)", min_value=0.0, max_value=1000.0, value=2.0)
    if st.button("Run backtest"):
        try:
            st.session_state["backtest"] = run_sma_backtest(df, fee_bps, slip_bps)
        except ValueError as ex:
            st.error(str(ex))
    bt = st.session_state.get("backtest")
    if bt:
        s1,s2,s3,s4 = st.columns(4)
        s1.metric("Strategy return", f"{bt['total_return']*100:.2f}%")
        s2.metric("Buy & hold", f"{bt['buy_hold_return']*100:.2f}%")
        s3.metric("Max drawdown", f"{bt['max_drawdown']*100:.2f}%")
        s4.metric("Entries", str(bt["trades"]))
        st.line_chart(pd.DataFrame(bt["curve"]).set_index("date"), y_label="Growth of 1 unit")
        st.write(f"Sharpe (0% risk-free assumption): {bt['sharpe']:.2f}" if bt["sharpe"] is not None else "Sharpe: N/A")
        st.caption(bt["note"])

with watch_tab:
    st.subheader("Saved watchlist")
    st.write("A watchlist is a list of tickers to analyze; it is not a live quote screen.")
    wl = store.list_watchlist(DB_PATH)
    st.dataframe(pd.DataFrame({"Ticker": wl}), hide_index=True)
    new = st.text_input("Add ticker", key="wl_new", placeholder="Example: AAPL")
    if st.button("Add ticker to watchlist") and new:
        try:
            store.add_watchlist(new, DB_PATH)
            st.rerun()
        except ValueError as e:
            st.error(str(e))
    rm = st.selectbox("Remove from watchlist", ["(none)"] + wl)
    if st.button("Remove selected") and rm != "(none)":
        store.remove_watchlist(rm, DB_PATH)
        st.rerun()

with portfolio_tab:
    st.subheader("Paper portfolio transaction ledger")
    st.caption("Simulated buys and sells only. Weighted-average cost basis, no broker connection, no tax lots.")
    with st.form("tx"):
        t = st.text_input("Ticker", value=symbol, key="tx_ticker")
        side = st.selectbox("Action", ["BUY", "SELL"])
        qty = st.number_input("Number of shares", min_value=0.001, value=1.0)
        price = st.number_input("Price per share", min_value=0.01, value=float(info["last_adj_close"]))
        fees = st.number_input("Fees", min_value=0.0, value=0.0)
        if st.form_submit_button("Record paper transaction"):
            try:
                store.add_transaction(t, side, qty, price, fees, DB_PATH)
                st.success("Saved local paper transaction. No real trade placed.")
            except ValueError as ex:
                st.error(str(ex))
    st.dataframe(pd.DataFrame(store.positions(DB_PATH)), hide_index=True, use_container_width=True)
    with st.expander("Transaction history"):
        st.dataframe(pd.DataFrame(store.transactions(DB_PATH)), hide_index=True, use_container_width=True)
    st.caption("Do not sum holdings from different currencies without an FX conversion.")

with alerts_tab:
    st.subheader("Manual local alert checks")
    st.caption("Thresholds are evaluated on the latest stored candle; no email or automatic background checks.")
    with st.form("alerts_form"):
        at = st.text_input("Ticker", value=symbol, key="alert_ticker")
        rule = st.selectbox("Rule", store.VALID_RULES)
        threshold = st.number_input("Threshold (not used for CLOSE_LT_BBLOWER)", value=30.0)
        if st.form_submit_button("Add alert"):
            try:
                store.add_alert(at, rule, threshold, DB_PATH)
                st.success("Alert stored locally.")
            except ValueError as ex:
                st.error(str(ex))
    if st.button("Check alerts now"):
        triggered = store.check_alerts(DB_PATH)
        st.success(f"Found {len(triggered)} new alert(s) for the latest stored dates.")
    st.dataframe(pd.DataFrame(store.list_alerts(DB_PATH)), hide_index=True, use_container_width=True)
    with st.expander("Triggered alert history"):
        st.dataframe(pd.DataFrame(store.alert_events(DB_PATH)), hide_index=True, use_container_width=True)
