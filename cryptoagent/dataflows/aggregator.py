"""Unified data interface for all agents."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from cryptoagent.dataflows.market.ccxt_provider import get_market_snapshot

logger = logging.getLogger(__name__)


class DataAggregator:
    """Collects data from all sources. Stubs return placeholder data for Phase 1."""

    def __init__(self, exchange: str = "binance") -> None:
        self.exchange = exchange

    def get_market_data(self, token: str) -> dict:
        """Fetch real market data via CCXT."""
        logger.info("Fetching market data for %s", token)
        return get_market_snapshot(token, self.exchange)

    def get_onchain_data(self, token: str) -> dict:
        """Stub: on-chain data (TVL, whale flows, etc.)."""
        return {
            "source": "stub",
            "token": token.upper(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "tvl_trend": "stable",
            "whale_activity": "low",
            "active_addresses_trend": "slightly_increasing",
            "note": "On-chain data not yet implemented. Using placeholder values.",
        }

    def get_sentiment_data(self, token: str) -> dict:
        """Stub: social/news sentiment data."""
        return {
            "source": "stub",
            "token": token.upper(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "twitter_sentiment": "neutral",
            "twitter_volume": "moderate",
            "reddit_sentiment": "slightly_bullish",
            "news_headlines": [
                f"{token.upper()} ecosystem shows continued development activity",
                f"Institutional interest in {token.upper()} remains steady",
            ],
            "fear_greed_index": 55,
            "fear_greed_label": "neutral",
            "note": "Sentiment data not yet implemented. Using placeholder values.",
        }

    def get_macro_data(self) -> dict:
        """Stub: macroeconomic data."""
        return {
            "source": "stub",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "dxy_trend": "stable",
            "fed_rate_outlook": "hold",
            "risk_appetite": "moderate",
            "sp500_trend": "slightly_bullish",
            "note": "Macro data not yet implemented. Using placeholder values.",
        }
