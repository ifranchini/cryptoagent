"""Market data provider using CCXT + ta (technical analysis)."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

import ccxt
import pandas as pd
import ta

logger = logging.getLogger(__name__)

# Map token symbols to CCXT trading pairs
_PAIR_MAP: dict[str, str] = {
    "SOL": "SOL/USDT",
    "BTC": "BTC/USDT",
    "ETH": "ETH/USDT",
}


def _get_pair(token: str) -> str:
    """Resolve token to a CCXT trading pair."""
    pair = _PAIR_MAP.get(token.upper())
    if pair is None:
        pair = f"{token.upper()}/USDT"
    return pair


def _add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Compute technical indicators on OHLCV dataframe."""
    close = df["close"]
    high = df["high"]
    low = df["low"]
    volume = df["volume"]

    # Trend
    df["sma_20"] = ta.trend.sma_indicator(close, window=20)
    df["sma_50"] = ta.trend.sma_indicator(close, window=50)
    df["ema_12"] = ta.trend.ema_indicator(close, window=12)
    df["ema_26"] = ta.trend.ema_indicator(close, window=26)

    # MACD
    macd = ta.trend.MACD(close)
    df["macd"] = macd.macd()
    df["macd_signal"] = macd.macd_signal()
    df["macd_histogram"] = macd.macd_diff()

    # RSI
    df["rsi_14"] = ta.momentum.rsi(close, window=14)

    # Bollinger Bands
    bb = ta.volatility.BollingerBands(close, window=20, window_dev=2)
    df["bb_upper"] = bb.bollinger_hband()
    df["bb_middle"] = bb.bollinger_mavg()
    df["bb_lower"] = bb.bollinger_lband()

    # ATR (volatility)
    df["atr_14"] = ta.volatility.average_true_range(high, low, close, window=14)

    # Volume
    df["volume_sma_20"] = ta.trend.sma_indicator(volume, window=20)

    return df


def fetch_ohlcv(
    token: str,
    exchange_id: str = "binance",
    timeframe: str = "1d",
    limit: int = 100,
) -> pd.DataFrame:
    """Fetch OHLCV candles from exchange via CCXT.

    Returns DataFrame with columns: timestamp, open, high, low, close, volume
    plus computed technical indicators.
    """
    exchange_class = getattr(ccxt, exchange_id)
    exchange = exchange_class({"enableRateLimit": True})

    pair = _get_pair(token)
    logger.info("Fetching %s %s from %s (limit=%d)", pair, timeframe, exchange_id, limit)

    raw = exchange.fetch_ohlcv(pair, timeframe=timeframe, limit=limit)

    df = pd.DataFrame(raw, columns=["timestamp", "open", "high", "low", "close", "volume"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
    df = df.set_index("timestamp")

    df = _add_indicators(df)
    df = df.dropna()

    logger.info("Fetched %d candles with indicators for %s", len(df), pair)
    return df


def get_market_snapshot(
    token: str,
    exchange_id: str = "binance",
) -> dict:
    """Get a complete market data snapshot for an asset.

    Returns a dict with daily and 4h data, current price, and key indicator values.
    """
    df_daily = fetch_ohlcv(token, exchange_id, timeframe="1d", limit=100)
    df_4h = fetch_ohlcv(token, exchange_id, timeframe="4h", limit=100)

    latest = df_daily.iloc[-1]
    prev = df_daily.iloc[-2]

    price_change_pct = ((latest["close"] - prev["close"]) / prev["close"]) * 100

    snapshot = {
        "token": token.upper(),
        "exchange": exchange_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "current_price": float(latest["close"]),
        "price_change_24h_pct": round(price_change_pct, 2),
        "volume_24h": float(latest["volume"]),
        "indicators": {
            "rsi_14": round(float(latest["rsi_14"]), 2),
            "macd": round(float(latest["macd"]), 4),
            "macd_signal": round(float(latest["macd_signal"]), 4),
            "macd_histogram": round(float(latest["macd_histogram"]), 4),
            "sma_20": round(float(latest["sma_20"]), 4),
            "sma_50": round(float(latest["sma_50"]), 4),
            "bb_upper": round(float(latest["bb_upper"]), 4),
            "bb_lower": round(float(latest["bb_lower"]), 4),
            "atr_14": round(float(latest["atr_14"]), 4),
        },
        "price_vs_sma20": "above" if latest["close"] > latest["sma_20"] else "below",
        "price_vs_sma50": "above" if latest["close"] > latest["sma_50"] else "below",
        "daily_ohlcv_last5": _df_to_records(df_daily.tail(5)),
        "four_hour_ohlcv_last10": _df_to_records(df_4h.tail(10)),
    }

    return snapshot


def _df_to_records(df: pd.DataFrame) -> list[dict]:
    """Convert DataFrame rows to list of dicts for serialization."""
    records = []
    for ts, row in df.iterrows():
        records.append(
            {
                "timestamp": ts.isoformat(),
                "open": round(float(row["open"]), 4),
                "high": round(float(row["high"]), 4),
                "low": round(float(row["low"]), 4),
                "close": round(float(row["close"]), 4),
                "volume": round(float(row["volume"]), 2),
                "rsi_14": round(float(row["rsi_14"]), 2),
                "macd": round(float(row["macd"]), 4),
            }
        )
    return records
