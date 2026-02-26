"""Extract structured signals from AgentState after each pipeline run."""

from __future__ import annotations

import json
import logging

logger = logging.getLogger(__name__)


def _safe_float(value: object, default: float = 0.0) -> float:
    """Convert a value to float, returning default on failure."""
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return default


def _direction_from_rsi(rsi: float) -> str:
    if rsi < 30:
        return "bullish"
    if rsi > 70:
        return "bearish"
    return "neutral"


def _confidence_from_rsi(rsi: float) -> float:
    """Confidence is higher the further from 50 (neutral zone)."""
    distance = abs(rsi - 50)
    return min(1.0, distance / 50)


def _direction_from_macd(histogram: float) -> str:
    if histogram > 0:
        return "bullish"
    if histogram < 0:
        return "bearish"
    return "neutral"


def _direction_from_sma(position: str) -> str:
    if position == "above":
        return "bullish"
    if position == "below":
        return "bearish"
    return "neutral"


def _direction_from_fear_greed(value: int) -> str:
    """Contrarian: extreme fear = bullish opportunity, extreme greed = bearish."""
    if value < 25:
        return "bullish"
    if value > 75:
        return "bearish"
    return "neutral"


def _direction_from_regime(regime: str) -> str:
    if regime in ("bull", "risk_on"):
        return "bullish"
    if regime in ("bear", "risk_off"):
        return "bearish"
    return "neutral"


def _direction_from_action(action: str) -> str:
    if action == "BUY":
        return "bullish"
    if action == "SELL":
        return "bearish"
    return "neutral"


def _extract_technical(market_data: dict) -> list[dict]:
    """Extract technical indicator signals from market_data."""
    indicators = market_data.get("indicators", {})
    if not indicators:
        return []

    signals: list[dict] = []

    # RSI
    rsi = _safe_float(indicators.get("rsi_14"))
    if rsi > 0:
        signals.append(
            {
                "name": "rsi_14",
                "source": "technical",
                "direction": _direction_from_rsi(rsi),
                "confidence": _confidence_from_rsi(rsi),
                "raw_value": rsi,
            }
        )

    # MACD histogram
    macd_hist = _safe_float(indicators.get("macd_histogram"))
    signals.append(
        {
            "name": "macd_histogram",
            "source": "technical",
            "direction": _direction_from_macd(macd_hist),
            "confidence": min(1.0, abs(macd_hist) / 5),
            "raw_value": macd_hist,
        }
    )

    # Price vs SMA20
    sma20_pos = market_data.get("price_vs_sma20", "")
    if sma20_pos:
        signals.append(
            {
                "name": "price_vs_sma20",
                "source": "technical",
                "direction": _direction_from_sma(sma20_pos),
                "confidence": 0.6,
                "raw_value": 1.0 if sma20_pos == "above" else -1.0,
            }
        )

    # Price vs SMA50
    sma50_pos = market_data.get("price_vs_sma50", "")
    if sma50_pos:
        signals.append(
            {
                "name": "price_vs_sma50",
                "source": "technical",
                "direction": _direction_from_sma(sma50_pos),
                "confidence": 0.7,
                "raw_value": 1.0 if sma50_pos == "above" else -1.0,
            }
        )

    # Bollinger Band position
    price = _safe_float(market_data.get("current_price"))
    bb_lower = _safe_float(indicators.get("bb_lower"))
    bb_upper = _safe_float(indicators.get("bb_upper"))
    if price > 0 and bb_lower > 0 and bb_upper > 0:
        if price < bb_lower:
            direction = "bullish"
        elif price > bb_upper:
            direction = "bearish"
        else:
            direction = "neutral"
        bb_range = bb_upper - bb_lower
        bb_mid = (bb_upper + bb_lower) / 2
        bb_confidence = (
            min(1.0, abs(price - bb_mid) / bb_range) if bb_range > 0 else 0.5
        )
        signals.append(
            {
                "name": "bb_position",
                "source": "technical",
                "direction": direction,
                "confidence": bb_confidence,
                "raw_value": price,
            }
        )

    return signals


def _extract_onchain(onchain_data: dict) -> list[dict]:
    """Extract on-chain signals from onchain_data."""
    if onchain_data.get("source") == "stub":
        return []

    signals: list[dict] = []

    # TVL trend from DeFiLlama
    defillama = onchain_data.get("defillama", {})
    tvl_change = _safe_float(defillama.get("solana_tvl_change_7d"))
    if tvl_change != 0:
        direction = "bullish" if tvl_change > 0 else "bearish"
        signals.append(
            {
                "name": "tvl_trend",
                "source": "onchain",
                "direction": direction,
                "confidence": min(1.0, abs(tvl_change) / 20),
                "raw_value": tvl_change,
            }
        )

    # Whale activity from Solana RPC
    solana = onchain_data.get("solana_network", {})
    whale_data = solana.get("whale_activity", {})
    # whale_activity can be a dict (real data) or string (stub)
    if isinstance(whale_data, dict):
        whale_level = whale_data.get("whale_activity_level", "")
    else:
        whale_level = str(whale_data) if whale_data else ""
    if whale_level and whale_level not in ("unknown", "error"):
        direction_map = {"high": "bullish", "moderate": "neutral", "low": "bearish"}
        raw_map = {"high": 1.0, "moderate": 0.0, "low": -1.0}
        signals.append(
            {
                "name": "whale_activity",
                "source": "onchain",
                "direction": direction_map.get(whale_level, "neutral"),
                "confidence": 0.5,
                "raw_value": raw_map.get(whale_level, 0.0),
            }
        )

    # DEX volume from DeFiLlama
    dex_vol_change = _safe_float(defillama.get("total_dex_volume_change_7d"))
    if dex_vol_change != 0:
        direction = "bullish" if dex_vol_change > 0 else "bearish"
        signals.append(
            {
                "name": "dex_volume",
                "source": "onchain",
                "direction": direction,
                "confidence": min(1.0, abs(dex_vol_change) / 30),
                "raw_value": dex_vol_change,
            }
        )

    return signals


def _extract_sentiment(state: dict) -> list[dict]:
    """Extract sentiment signals from state."""
    signals: list[dict] = []

    # Fear & Greed Index (contrarian)
    fng = state.get("fear_greed_index", 50)
    fng_val = int(fng) if fng else 50
    signals.append(
        {
            "name": "fear_greed",
            "source": "sentiment",
            "direction": _direction_from_fear_greed(fng_val),
            "confidence": min(1.0, abs(fng_val - 50) / 50),
            "raw_value": float(fng_val),
        }
    )

    # Reddit sentiment from sentiment report
    sentiment_report = state.get("sentiment_report", "")
    if "bullish" in sentiment_report.lower():
        signals.append(
            {
                "name": "reddit_sentiment",
                "source": "sentiment",
                "direction": "bullish",
                "confidence": 0.4,
                "raw_value": 1.0,
            }
        )
    elif "bearish" in sentiment_report.lower():
        signals.append(
            {
                "name": "reddit_sentiment",
                "source": "sentiment",
                "direction": "bearish",
                "confidence": 0.4,
                "raw_value": -1.0,
            }
        )

    return signals


def _extract_macro(state: dict) -> list[dict]:
    """Extract macro signals from state."""
    signals: list[dict] = []

    macro_regime = state.get("macro_regime", "unknown")
    if macro_regime != "unknown":
        signals.append(
            {
                "name": "macro_regime",
                "source": "macro",
                "direction": _direction_from_regime(macro_regime),
                "confidence": 0.6,
                "raw_value": {"risk_on": 1.0, "risk_off": -1.0, "neutral": 0.0}.get(
                    macro_regime, 0.0
                ),
            }
        )

    market_regime = state.get("market_regime", "unknown")
    if market_regime != "unknown":
        signals.append(
            {
                "name": "market_regime",
                "source": "macro",
                "direction": _direction_from_regime(market_regime),
                "confidence": state.get("regime_confidence", 5) / 10,
                "raw_value": {"bull": 1.0, "bear": -1.0, "sideways": 0.0}.get(
                    market_regime, 0.0
                ),
            }
        )

    regime_conf = state.get("regime_confidence", 0)
    if regime_conf > 0:
        signals.append(
            {
                "name": "regime_confidence",
                "source": "macro",
                "direction": "neutral",
                "confidence": regime_conf / 10,
                "raw_value": float(regime_conf),
            }
        )

    return signals


def _extract_brain(state: dict) -> list[dict]:
    """Extract signals from the Brain decision."""
    brain_raw = state.get("brain_decision", "")
    if not brain_raw:
        return []

    try:
        brain = json.loads(brain_raw)
    except (json.JSONDecodeError, TypeError):
        return []

    signals: list[dict] = []

    action = brain.get("action", "HOLD")
    signals.append(
        {
            "name": "brain_action",
            "source": "brain",
            "direction": _direction_from_action(action),
            "confidence": brain.get("confidence", 5) / 10,
            "raw_value": {"BUY": 1.0, "SELL": -1.0, "HOLD": 0.0}.get(action, 0.0),
        }
    )

    confidence = brain.get("confidence", 0)
    if confidence > 0:
        signals.append(
            {
                "name": "brain_confidence",
                "source": "brain",
                "direction": _direction_from_action(action),
                "confidence": confidence / 10,
                "raw_value": float(confidence),
            }
        )

    size_pct = _safe_float(brain.get("size_pct"))
    if size_pct > 0:
        signals.append(
            {
                "name": "brain_size_pct",
                "source": "brain",
                "direction": _direction_from_action(action),
                "confidence": min(1.0, size_pct / 50),
                "raw_value": size_pct,
            }
        )

    brain_regime = brain.get("regime", "")
    if brain_regime:
        signals.append(
            {
                "name": "brain_regime",
                "source": "brain",
                "direction": _direction_from_regime(brain_regime),
                "confidence": confidence / 10 if confidence > 0 else 0.5,
                "raw_value": {"bull": 1.0, "bear": -1.0, "sideways": 0.0}.get(
                    brain_regime, 0.0
                ),
            }
        )

    return signals


def extract_signals(state: dict) -> list[dict]:
    """Extract all structured signals from a completed AgentState.

    Returns a list of signal dicts, each with: name, source, direction,
    confidence (0.0-1.0), and raw_value.
    """
    # Ensure we work with plain dicts (LangGraph may return special types)
    market_data = dict(state.get("market_data") or {})
    onchain_data = dict(state.get("onchain_data") or {})

    signals: list[dict] = []

    signals.extend(_extract_technical(market_data))
    signals.extend(_extract_onchain(onchain_data))
    signals.extend(_extract_sentiment(state))
    signals.extend(_extract_macro(state))
    signals.extend(_extract_brain(state))

    logger.info("Extracted %d signals from pipeline state", len(signals))
    return signals
