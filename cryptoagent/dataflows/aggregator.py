"""Unified data interface for all agents."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from cryptoagent.config import AgentConfig
from cryptoagent.dataflows.market.ccxt_provider import get_market_snapshot
from cryptoagent.dataflows.onchain.defillama import get_all_onchain_data
from cryptoagent.dataflows.onchain.fear_greed import get_fear_greed_index
from cryptoagent.dataflows.onchain.solana_rpc import get_solana_network_data
from cryptoagent.dataflows.social.reddit import get_reddit_sentiment
from cryptoagent.dataflows.social.twitter import get_twitter_sentiment
from cryptoagent.dataflows import regime

logger = logging.getLogger(__name__)

_ONCHAIN_STUB = {
    "source": "stub",
    "note": "On-chain data unavailable. Using placeholder values.",
    "tvl_trend": "stable",
    "whale_activity": "low",
}

_SENTIMENT_STUB = {
    "source": "stub",
    "note": "Sentiment data unavailable. Using placeholder values.",
    "twitter_sentiment": "neutral",
    "reddit_sentiment": "neutral",
    "fear_greed_index": 50,
    "fear_greed_label": "neutral",
}


class DataAggregator:
    """Collects data from all sources — real providers with stub fallbacks."""

    def __init__(self, exchange: str = "binance", config: AgentConfig | None = None) -> None:
        self.exchange = exchange
        self._config = config or AgentConfig()

    def get_market_data(self, token: str) -> dict:
        """Fetch real market data via CCXT."""
        logger.info("Fetching market data for %s", token)
        return get_market_snapshot(token, self.exchange)

    def get_onchain_data(self, token: str) -> dict:
        """Fetch real on-chain data from DeFiLlama + Solana RPC.

        Falls back to stub on any failure.
        """
        logger.info("Fetching on-chain data for %s", token)
        try:
            defillama = get_all_onchain_data(self._config.defillama_base_url)
            solana = get_solana_network_data(self._config.solana_rpc_url)

            return {
                "source": "real",
                "token": token.upper(),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "defillama": defillama,
                "solana_network": solana,
            }
        except Exception as e:
            logger.warning("On-chain data fetch failed, using stub: %s", e)
            return {**_ONCHAIN_STUB, "token": token.upper(), "timestamp": datetime.now(timezone.utc).isoformat()}

    def get_sentiment_data(self, token: str) -> dict:
        """Fetch real sentiment from Reddit, X/Twitter, and Fear & Greed.

        Falls back to stub on any failure.
        """
        logger.info("Fetching sentiment data for %s", token)
        try:
            reddit = get_reddit_sentiment(
                subreddits=self._config.reddit_subreddits,
                token=token,
            )
            twitter = get_twitter_sentiment(
                token=token,
                bearer_token=self._config.twitter_bearer_token,
                scrape_url=self._config.twitter_scrape_url,
            )
            fng = get_fear_greed_index()

            fng_value = fng.get("value", 50) if fng.get("source") != "error" else 50
            fng_label = fng.get("classification", "Neutral") if fng.get("source") != "error" else "Neutral"

            return {
                "source": "real",
                "token": token.upper(),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "reddit": reddit,
                "twitter": twitter,
                "fear_greed_index": fng_value,
                "fear_greed_label": fng_label,
            }
        except Exception as e:
            logger.warning("Sentiment data fetch failed, using stub: %s", e)
            return {**_SENTIMENT_STUB, "token": token.upper(), "timestamp": datetime.now(timezone.utc).isoformat()}

    def get_market_regime(self, market_data: dict) -> dict:
        """Classify market regime from technical indicators."""
        indicators = market_data.get("indicators", {})
        indicators["current_price"] = market_data.get("current_price", 0)
        return regime.classify(indicators)

    def get_macro_data(self) -> dict:
        """Stub: macroeconomic data (not yet replaced in Phase 2)."""
        return {
            "source": "stub",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "dxy_trend": "stable",
            "fed_rate_outlook": "hold",
            "risk_appetite": "moderate",
            "sp500_trend": "slightly_bullish",
            "note": "Macro data not yet implemented. Using placeholder values.",
        }
