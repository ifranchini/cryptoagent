"""FRED API client for macroeconomic data."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

import httpx

logger = logging.getLogger(__name__)

_BASE_URL = "https://api.stlouisfed.org/fred/series/observations"
_TIMEOUT = 10


def _fetch_series(
    api_key: str,
    series_id: str,
    limit: int = 12,
) -> list[dict]:
    """Fetch recent observations for a FRED series.

    Returns list of {"date": str, "value": str} dicts, newest first.
    """
    params = {
        "series_id": series_id,
        "api_key": api_key,
        "file_type": "json",
        "sort_order": "desc",
        "limit": limit,
    }
    resp = httpx.get(_BASE_URL, params=params, timeout=_TIMEOUT)
    resp.raise_for_status()
    return resp.json().get("observations", [])


def _safe_float(value: str) -> float | None:
    """Parse FRED value, returning None for missing data ('.')."""
    if value in (".", ""):
        return None
    try:
        return float(value)
    except ValueError:
        return None


def _trend(latest: float | None, earlier: float | None) -> str:
    """Compare two values and return a directional label."""
    if latest is None or earlier is None:
        return "unknown"
    diff = latest - earlier
    threshold = abs(earlier) * 0.005 if earlier != 0 else 0.01
    if diff > threshold:
        return "expanding" if "m2" in "" else "rising"
    if diff < -threshold:
        return "contracting" if "m2" in "" else "falling"
    return "stable"


def _compute_trend(
    observations: list[dict],
    offset: int,
    rising_label: str = "rising",
    falling_label: str = "falling",
) -> str:
    """Compare latest observation vs one at `offset` positions back."""
    if len(observations) < offset + 1:
        return "unknown"
    latest = _safe_float(observations[0].get("value", "."))
    earlier = _safe_float(observations[offset].get("value", "."))
    if latest is None or earlier is None:
        return "unknown"
    diff = latest - earlier
    threshold = abs(earlier) * 0.005 if earlier != 0 else 0.01
    if diff > threshold:
        return rising_label
    if diff < -threshold:
        return falling_label
    return "stable"


def get_m2_money_supply(api_key: str) -> dict:
    """Fetch M2 money supply (monthly, seasonally adjusted)."""
    try:
        obs = _fetch_series(api_key, "M2SL", limit=6)
        latest = _safe_float(obs[0]["value"]) if obs else None
        trend = _compute_trend(obs, 3, "expanding", "contracting")
        return {
            "source": "fred",
            "series": "M2SL",
            "latest_value": latest,
            "latest_date": obs[0]["date"] if obs else None,
            "trend_3m": trend,
            "unit": "billions_usd",
        }
    except Exception as e:
        logger.warning("FRED M2 fetch failed: %s", e)
        return {"source": "error", "series": "M2SL", "message": str(e)}


def get_fed_funds_rate(api_key: str) -> dict:
    """Fetch effective Federal Funds Rate (monthly)."""
    try:
        obs = _fetch_series(api_key, "FEDFUNDS", limit=8)
        latest = _safe_float(obs[0]["value"]) if obs else None
        trend = _compute_trend(obs, 6, "rising", "falling")
        return {
            "source": "fred",
            "series": "FEDFUNDS",
            "latest_value": latest,
            "latest_date": obs[0]["date"] if obs else None,
            "direction_6m": trend,
            "unit": "percent",
        }
    except Exception as e:
        logger.warning("FRED Fed Funds fetch failed: %s", e)
        return {"source": "error", "series": "FEDFUNDS", "message": str(e)}


def get_treasury_yields(api_key: str) -> dict:
    """Fetch 10-Year and 2-Year Treasury yields."""
    try:
        gs10 = _fetch_series(api_key, "GS10", limit=3)
        gs2 = _fetch_series(api_key, "GS2", limit=3)
        return {
            "source": "fred",
            "ten_year": _safe_float(gs10[0]["value"]) if gs10 else None,
            "two_year": _safe_float(gs2[0]["value"]) if gs2 else None,
            "ten_year_date": gs10[0]["date"] if gs10 else None,
            "two_year_date": gs2[0]["date"] if gs2 else None,
            "unit": "percent",
        }
    except Exception as e:
        logger.warning("FRED Treasury yields fetch failed: %s", e)
        return {"source": "error", "series": "GS10/GS2", "message": str(e)}


def get_yield_spread(api_key: str) -> dict:
    """Fetch 10Y-2Y yield spread (yield curve inversion signal)."""
    try:
        obs = _fetch_series(api_key, "T10Y2Y", limit=3)
        latest = _safe_float(obs[0]["value"]) if obs else None
        curve_status = "unknown"
        if latest is not None:
            curve_status = "normal" if latest > 0 else "inverted"
        return {
            "source": "fred",
            "series": "T10Y2Y",
            "latest_value": latest,
            "latest_date": obs[0]["date"] if obs else None,
            "yield_curve": curve_status,
            "unit": "percent",
        }
    except Exception as e:
        logger.warning("FRED yield spread fetch failed: %s", e)
        return {"source": "error", "series": "T10Y2Y", "message": str(e)}


def get_all_macro_data(api_key: str) -> dict:
    """Aggregate all FRED macro data into a single dict."""
    if not api_key:
        return {
            "source": "error",
            "message": "No FRED API key configured",
        }

    m2 = get_m2_money_supply(api_key)
    fed = get_fed_funds_rate(api_key)
    yields = get_treasury_yields(api_key)
    spread = get_yield_spread(api_key)

    return {
        "source": "fred",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "m2_money_supply": m2,
        "fed_funds_rate": fed,
        "treasury_yields": yields,
        "yield_spread": spread,
    }
