"""Static, printable charts (true saved outputs, never mock screenshots)."""
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


def create_charts(df: pd.DataFrame, ticker: str, directory: Path) -> list[Path]:
    directory.mkdir(parents=True, exist_ok=True)
    x = pd.to_datetime(df["date"])
    output = []

    fig, ax = plt.subplots(figsize=(11, 5))
    ax.plot(x, df["adj_close"], linewidth=1.6, label="Adjusted close")
    ax.set(title=f"{ticker} | Price history", xlabel="Date", ylabel="Price (ticker currency / demo units)")
    ax.legend()
    ax.grid(alpha=0.2)
    fig.autofmt_xdate()
    fig.tight_layout()
    path = directory / f"{ticker}_price.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    output.append(path)

    fig, ax = plt.subplots(figsize=(11, 5))
    ax.plot(x, df["adj_close"], label="Adjusted close", alpha=0.6)
    ax.plot(x, df["sma20"], label="SMA20")
    ax.plot(x, df["sma50"], label="SMA50")
    ax.set(title=f"{ticker} | Moving averages", xlabel="Date", ylabel="Price")
    ax.legend()
    ax.grid(alpha=0.2)
    fig.autofmt_xdate()
    fig.tight_layout()
    path = directory / f"{ticker}_moving_averages.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    output.append(path)

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.hist(df["daily_return"].dropna() * 100, bins=40, edgecolor="white")
    ax.set(title=f"{ticker} | Daily returns", xlabel="Daily adjusted return (%)", ylabel="Trading days")
    ax.grid(axis="y", alpha=0.2)
    fig.tight_layout()
    path = directory / f"{ticker}_daily_returns.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    output.append(path)
    return output
