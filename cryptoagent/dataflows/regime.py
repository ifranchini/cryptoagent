"""Market regime classifier — pure numeric heuristic, no LLM calls."""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def classify(indicators: dict) -> dict:
    """Classify market regime from technical indicators.

    Args:
        indicators: Dict with keys from market_data["indicators"] plus current_price.
            Expected: current_price, sma_50, rsi_14, macd_histogram, atr_14, sma_20

    Returns:
        {"regime": str, "confidence": int (1-10), "signals": {...}}
    """
    price = indicators.get("current_price", 0)
    sma50 = indicators.get("sma_50", 0)
    rsi = indicators.get("rsi_14", 50)
    macd_hist = indicators.get("macd_histogram", 0)
    atr = indicators.get("atr_14", 0)
    sma20 = indicators.get("sma_20", 0)

    if not price or not sma50:
        return {"regime": "unknown", "confidence": 1, "signals": {"error": "insufficient data"}}

    signals = {
        "price_above_sma50": price > sma50,
        "rsi_above_50": rsi > 50,
        "macd_positive": macd_hist > 0,
        "price_above_sma20": price > sma20,
    }

    bull_count = sum(signals.values())
    total_signals = len(signals)

    # Classify regime
    if bull_count >= 3:
        regime = "bull"
        confidence = min(10, 5 + bull_count)
    elif bull_count <= 1:
        regime = "bear"
        confidence = min(10, 5 + (total_signals - bull_count))
    else:
        regime = "sideways"
        # Low ATR relative to price confirms sideways
        atr_pct = (atr / price * 100) if price > 0 else 0
        confidence = 7 if atr_pct < 2 else 5

    # RSI extremes boost confidence
    if rsi > 70 and regime == "bull":
        confidence = min(10, confidence + 1)
    elif rsi < 30 and regime == "bear":
        confidence = min(10, confidence + 1)

    signals["rsi_value"] = round(rsi, 2)
    signals["macd_histogram"] = round(macd_hist, 4)
    signals["atr_pct_of_price"] = round((atr / price * 100) if price > 0 else 0, 2)

    return {
        "regime": regime,
        "confidence": confidence,
        "signals": signals,
    }
