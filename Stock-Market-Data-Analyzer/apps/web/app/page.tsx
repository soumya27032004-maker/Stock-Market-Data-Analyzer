'use client';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { ResponsiveContainer, LineChart, Line, CartesianGrid, Legend, Tooltip, XAxis, YAxis } from 'recharts';

type Price = { date: string; adj_close: number; sma20: number|null; sma50: number|null; rsi14: number|null; daily_return: number|null };
type Equity = { date: string; strategy: number; buy_hold: number };
type Bt = { total_return: number; buy_hold_return: number; max_drawdown: number; sharpe: number|null; trades: number; closed_trades: number; win_rate: number|null; curve: Equity[]; note: string };
type Position = { ticker: string; quantity: number; average_cost: number; cost_basis: number; realized_pnl: number };
type Alert = { id: string; ticker: string; rule: string; threshold: number; last_fired_date: string|null };
type AlertEvent = { id: string; message: string; date: string };

type Tab = 'Overview' | 'Backtest' | 'Watchlist' | 'Paper portfolio' | 'Alerts';
const tabs: Tab[] = ['Overview', 'Backtest', 'Watchlist', 'Paper portfolio', 'Alerts'];

async function api<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`/api${url}`, { cache: 'no-store', ...init });
  const payload = await response.json();
  if (!response.ok) throw new Error(typeof payload.detail === 'string' ? payload.detail : `API returned ${response.status}`);
  return payload as T;
}
const jsonPost = (body: unknown): RequestInit => ({
  method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body)
});
const pct = (x: number | null | undefined) => x == null ? 'N/A' : `${(100*x).toFixed(2)}%`;

export default function Home() {
  const [ticker, setTicker] = useState('DEMO_AAPL');
  const [source, setSource] = useState<'sample'|'yahoo'>('sample');
  const [rows, setRows] = useState<Price[]>([]);
  const [bt, setBt] = useState<Bt|null>(null);
  const [watchlist, setWatchlist] = useState<string[]>([]);
  const [positions, setPositions] = useState<Position[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [events, setEvents] = useState<AlertEvent[]>([]);
  const [tab, setTab] = useState<Tab>('Overview');
  const [message, setMessage] = useState('Synthetic demo works offline after starting the Python API.');
  const [busy, setBusy] = useState(false);
  const [side, setSide] = useState<'BUY'|'SELL'>('BUY');
  const [qty, setQty] = useState(1);
  const [price, setPrice] = useState(100);
  const [rule, setRule] = useState('RSI_BELOW');
  const [threshold, setThreshold] = useState(30);
  const [fee, setFee] = useState(5);
  const [slippage, setSlippage] = useState(2);

  const loadAux = useCallback(async () => {
    const [w, p, a, e] = await Promise.all([
      api<string[]>('/watchlist'), api<Position[]>('/portfolio/positions'),
      api<Alert[]>('/alerts'), api<AlertEvent[]>('/alerts/events'),
    ]);
    setWatchlist(w); setPositions(p); setAlerts(a); setEvents(e);
  }, []);

  const loadChart = useCallback(async (symbol: string) => {
    const data = await api<Price[]>(`/chart/${encodeURIComponent(symbol.toUpperCase().trim())}?days=1000`);
    setRows(data); setBt(null);
  }, []);

  useEffect(() => {
    Promise.all([loadChart('DEMO_AAPL'), loadAux()]).catch(e => setMessage(`Connect the Python API on port 8000: ${e.message}`));
  }, [loadChart, loadAux]);

  const call = async (job: () => Promise<void>) => {
    setBusy(true);
    try { await job(); }
    catch (e) { setMessage(`Error: ${e instanceof Error ? e.message : String(e)}`); }
    finally { setBusy(false); }
  };

  const reload = () => call(async () => {
    const sym = ticker.toUpperCase().trim();
    if (source === 'sample' && !sym.startsWith('DEMO_')) throw new Error('Choose a DEMO_ symbol for sample mode.');
    await api(`/refresh/${encodeURIComponent(sym)}`, jsonPost({ source, start: '2024-01-01' }));
    await loadChart(sym); await loadAux();
    setMessage(`${sym} updated from ${source}. Yahoo history may be delayed.`);
  });

  const summary = useMemo(() => {
    if (!rows.length) return null;
    const first = rows[0]; const last = rows[rows.length - 1];
    return { first, last, change: last.adj_close / first.adj_close - 1 };
  }, [rows]);

  return <main className="shell">
    <header className="top"><div className="logo">SM<span>DA</span></div><div><h1>Stock Market Data Analyzer</h1><p>Historical research · Strategy sandbox · Local paper portfolio</p></div><a className="docs" href="http://127.0.0.1:8000/docs" target="_blank" rel="noreferrer">API docs ↗</a></header>
    <div className="notice">EDUCATIONAL ONLY • Synthetic DEMO symbols are not real securities • Yahoo data can be delayed • No real orders</div>
    <section className="toolbar">
      <label>Symbol<input aria-label="Ticker" value={ticker} onChange={e => setTicker(e.target.value.toUpperCase())} placeholder="DEMO_AAPL / AAPL" /></label>
      <label>Source<select value={source} onChange={e => setSource(e.target.value as 'sample'|'yahoo')}><option value="sample">Offline sample</option><option value="yahoo">Yahoo history</option></select></label>
      <button disabled={busy} onClick={reload}>{busy ? 'Working…' : 'Fetch / refresh'}</button>
      <span className="toolbarNote">e.g. RELIANCE.NS or AAPL in Yahoo mode</span>
    </section>
    <div className="status" role="status">{message}</div>
    <nav className="tabs" aria-label="Analyzer sections">{tabs.map(t => <button key={t} onClick={() => setTab(t)} className={tab === t ? 'active' : ''}>{t}</button>)}</nav>

    {tab === 'Overview' && <>
      <section className="stats">
        <div className="stat"><span>Latest adjusted close</span><b>{summary ? summary.last.adj_close.toFixed(2) : '—'}</b></div>
        <div className="stat"><span>Selected history change</span><b>{summary ? pct(summary.change) : '—'}</b></div>
        <div className="stat"><span>RSI (14)</span><b>{summary?.last.rsi14?.toFixed(1) ?? '—'}</b></div>
        <div className="stat"><span>Daily observations</span><b>{rows.length}</b></div>
      </section>
      <section className="panel"><h2>Adjusted close · SMA 20 · SMA 50</h2>{rows.length ? <div className="chart"><ResponsiveContainer width="100%" height="100%"><LineChart data={rows} margin={{top:10,right:15,bottom:10,left:0}}><CartesianGrid strokeDasharray="3 3" stroke="#dbe4ec"/><XAxis dataKey="date" minTickGap={45} tick={{fontSize:11}}/><YAxis domain={['auto','auto']} tick={{fontSize:11}}/><Tooltip/><Legend/><Line type="monotone" dataKey="adj_close" name="Adjusted close" dot={false} stroke="#2563eb" strokeWidth={2}/><Line type="monotone" dataKey="sma20" name="SMA 20" dot={false} stroke="#f59e0b" strokeWidth={1.5}/><Line type="monotone" dataKey="sma50" name="SMA 50" dot={false} stroke="#12a594" strokeWidth={1.5}/></LineChart></ResponsiveContainer></div> : <p>Start the Python API to see saved demo data.</p>}</section>
      <section className="panel"><h2>Latest daily rows</h2><div className="scroll"><table><thead><tr><th>Date</th><th>Adj close</th><th>SMA 20</th><th>SMA 50</th><th>Daily return</th></tr></thead><tbody>{rows.slice(-10).reverse().map(r => <tr key={r.date}><td>{r.date}</td><td>{r.adj_close.toFixed(2)}</td><td>{r.sma20?.toFixed(2) ?? '—'}</td><td>{r.sma50?.toFixed(2) ?? '—'}</td><td>{r.daily_return == null ? '—' : pct(r.daily_return)}</td></tr>)}</tbody></table></div></section>
    </>}

    {tab === 'Backtest' && <section className="panel"><h2>Long-only moving-average crossover</h2><p className="muted">Signals use the previous day's information. Returns are simplified close-to-close estimates, net of modeled costs.</p><div className="controls"><label>Fee (bps)<input type="number" min={0} value={fee} onChange={e => setFee(Number(e.target.value))}/></label><label>Slippage (bps)<input type="number" min={0} value={slippage} onChange={e => setSlippage(Number(e.target.value))}/></label><button disabled={busy} onClick={() => call(async () => { const result = await api<{stats:Bt}>('/backtest/sma', jsonPost({ticker,fee_bps:fee,slippage_bps:slippage}));setBt(result.stats);setMessage('Backtest complete. These are historical simulated results, not forecasts.'); })}>Run backtest</button></div>
      {bt && <><div className="stats"><div className="stat"><span>Strategy return</span><b>{pct(bt.total_return)}</b></div><div className="stat"><span>Buy & hold</span><b>{pct(bt.buy_hold_return)}</b></div><div className="stat"><span>Max drawdown</span><b>{pct(bt.max_drawdown)}</b></div><div className="stat"><span>Trade entries</span><b>{bt.trades}</b></div></div><div className="chart"><ResponsiveContainer width="100%" height="100%"><LineChart data={bt.curve}><CartesianGrid strokeDasharray="3 3"/><XAxis dataKey="date" minTickGap={45} tick={{fontSize:11}}/><YAxis tick={{fontSize:11}}/><Tooltip/><Legend/><Line name="Strategy" dataKey="strategy" stroke="#2563eb" dot={false}/><Line name="Buy and hold" dataKey="buy_hold" stroke="#10b981" dot={false}/></LineChart></ResponsiveContainer></div><p className="muted">Sharpe: {bt.sharpe?.toFixed(2) ?? 'N/A'} · Closed-trade win rate: {pct(bt.win_rate)} · {bt.note}</p></>}
    </section>}

    {tab === 'Watchlist' && <section className="panel"><h2>Your watchlist</h2><p className="muted">Saved tickers, not a streaming quote service. Click one to inspect its stored history.</p><div className="watchgrid">{watchlist.map(sym => <div className="watch" key={sym}><strong>{sym}</strong><div><button className="ghost" disabled={busy} onClick={() => call(async () => { setTicker(sym); await loadChart(sym); setTab('Overview'); })}>View</button><button className="danger ghost" disabled={busy} onClick={() => call(async () => { await api(`/watchlist/${encodeURIComponent(sym)}`,{method:'DELETE'});await loadAux(); })}>Remove</button></div></div>)}</div><button onClick={() => call(async () => { await api('/watchlist', jsonPost({ticker}));await loadAux(); })}>Add current ticker</button></section>}

    {tab === 'Paper portfolio' && <section className="panel"><h2>Record a paper transaction</h2><p className="muted">No broker connection. Quantities and moving-average cost are local only; currencies are not converted.</p><div className="controls"><label>Side<select value={side} onChange={e => setSide(e.target.value as 'BUY'|'SELL')}><option>BUY</option><option>SELL</option></select></label><label>Shares<input type="number" min="0.001" step="0.001" value={qty} onChange={e => setQty(Number(e.target.value))}/></label><label>Price<input type="number" min="0.01" step="0.01" value={price} onChange={e => setPrice(Number(e.target.value))}/></label><button disabled={busy} onClick={() => call(async () => { await api('/portfolio/transactions', jsonPost({ticker,side,qty,price,fees:0}));await loadAux();setMessage('Paper transaction saved; no real order placed.'); })}>Save paper trade</button></div><div className="scroll"><table><thead><tr><th>Symbol</th><th>Shares held</th><th>Average cost</th><th>Realized P&amp;L*</th></tr></thead><tbody>{positions.map(p => <tr key={p.ticker}><td>{p.ticker}</td><td>{p.quantity.toFixed(3)}</td><td>{p.average_cost.toFixed(2)}</td><td>{p.realized_pnl.toFixed(2)}</td></tr>)}</tbody></table></div><p className="muted">*In each ticker's original currency/demo units. This is not tax accounting.</p></section>}

    {tab === 'Alerts' && <section className="panel"><h2>Local threshold alerts</h2><p className="muted">Manual checks on the last stored candle only. No automatic email/SMS messages.</p><div className="controls"><label>Rule<select value={rule} onChange={e => setRule(e.target.value)}><option>RSI_BELOW</option><option>RSI_ABOVE</option><option>CLOSE_ABOVE</option><option>CLOSE_BELOW</option><option>CLOSE_LT_BBLOWER</option></select></label><label>Threshold<input type="number" value={threshold} onChange={e => setThreshold(Number(e.target.value))}/></label><button disabled={busy} onClick={() => call(async () => {await api('/alerts',jsonPost({ticker,rule,threshold}));await loadAux();setMessage('Alert rule saved.');})}>Add alert</button><button className="secondary" disabled={busy} onClick={() => call(async () => {const result = await api<{events: AlertEvent[]}>('/alerts/check',{method:'POST'});await loadAux();setMessage(`${result.events.length} new alert(s) triggered on stored data.`);})}>Check alerts now</button></div><div className="scroll"><table><thead><tr><th>Ticker</th><th>Rule</th><th>Threshold</th><th>Last triggered date</th></tr></thead><tbody>{alerts.map(a => <tr key={a.id}><td>{a.ticker}</td><td>{a.rule}</td><td>{a.threshold}</td><td>{a.last_fired_date ?? '—'}</td></tr>)}</tbody></table></div><h3>Alert history</h3>{events.slice(0,10).map(event => <p key={event.id} className="event">{event.message}</p>)}{events.length === 0 && <p className="muted">No fired alerts yet.</p>}</section>}
    <footer>Built for Python/FinTech learning · CSV + Yahoo Finance + SQLite + FastAPI + Next.js · Not financial advice</footer>
  </main>;
}
