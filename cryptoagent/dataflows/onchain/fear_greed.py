"""Alternative.me Fear & Greed Index for crypto market sentiment."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

import httpx

logger = logging.getLogger(__name__)

_TIMEOUT = 10
_URL = "https://api.alternative.me/fng/"


def get_fear_greed_index() -> dict:
    """Fetch the current Crypto Fear & Greed Index (0-100).

    0 = Extreme Fear, 100 = Extreme Greed.
    Returns dict with value, label, and timestamp.
    """
    try:
        with httpx.Client(timeout=_TIMEOUT) as client:
            resp = client.get(_URL, params={"limit": 1})
            resp.raise_for_status()
            data = resp.json()

        entry = data.get("data", [{}])[0]
        value = int(entry.get("value", 50))
        classification = entry.get("value_classification", "Neutral")

        return {
            "source": "alternative.me",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "value": value,
            "classification": classification,
        }
    except Exception as e:
        logger.warning("Fear & Greed Index failed: %s", e)
        return {"source": "error", "message": str(e)}
