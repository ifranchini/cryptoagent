"""Macro regime classifier — heuristic-based risk-on/risk-off classification."""

from __future__ import annotations


def classify_macro(macro_data: dict) -> dict:
    """Classify macro environment as risk-on, risk-off, or neutral.

    Counts bullish (risk-on) vs bearish (risk-off) signals from FRED data
    and returns a regime label with confidence.

    Args:
        macro_data: Output from ``get_all_macro_data``.

    Returns:
        Dict with ``macro_regime``, ``confidence`` (1-10), and ``signals``.
    """
    if macro_data.get("source") == "error":
        return {
            "macro_regime": "unknown",
            "confidence": 0,
            "signals": {"note": "Macro data unavailable"},
        }

    risk_on = 0
    risk_off = 0
    signals: dict[str, str] = {}

    # M2 money supply trend
    m2 = macro_data.get("m2_money_supply", {})
    m2_trend = m2.get("trend_3m", "unknown")
    signals["m2_trend"] = m2_trend
    if m2_trend == "expanding":
        risk_on += 1
    elif m2_trend == "contracting":
        risk_off += 1

    # Fed Funds Rate direction
    fed = macro_data.get("fed_funds_rate", {})
    fed_dir = fed.get("direction_6m", "unknown")
    fed_value = fed.get("latest_value")
    signals["fed_rate_direction"] = fed_dir
    if fed_dir in ("falling", "stable"):
        risk_on += 1
    elif fed_dir == "rising":
        risk_off += 1

    # Fed rate level
    if fed_value is not None:
        if fed_value < 3.0:
            signals["fed_rate_level"] = "low"
            risk_on += 1
        elif fed_value > 5.0:
            signals["fed_rate_level"] = "high"
            risk_off += 1
        else:
            signals["fed_rate_level"] = "moderate"

    # Yield curve
    spread = macro_data.get("yield_spread", {})
    curve = spread.get("yield_curve", "unknown")
    signals["yield_curve"] = curve
    if curve == "normal":
        risk_on += 1
    elif curve == "inverted":
        risk_off += 1

    # Classify
    total = risk_on + risk_off
    if total == 0:
        return {
            "macro_regime": "unknown",
            "confidence": 0,
            "signals": signals,
        }

    if risk_on > risk_off:
        regime = "risk_on"
        confidence = min(10, round((risk_on / total) * 10))
    elif risk_off > risk_on:
        regime = "risk_off"
        confidence = min(10, round((risk_off / total) * 10))
    else:
        regime = "neutral"
        confidence = 5

    return {
        "macro_regime": regime,
        "confidence": confidence,
        "signals": signals,
    }
