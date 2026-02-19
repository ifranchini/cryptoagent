"""X/Twitter sentiment — dual-backend: scraping proxy or official API v2."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

import httpx

logger = logging.getLogger(__name__)

_TIMEOUT = 15


class ScrapingBackend:
    """Fetches tweets via a configurable scraping proxy URL."""

    def __init__(self, scrape_url: str) -> None:
        self._url = scrape_url

    def search(self, query: str, limit: int = 20) -> list[dict]:
        try:
            with httpx.Client(timeout=_TIMEOUT) as client:
                resp = client.get(
                    self._url,
                    params={"q": query, "limit": limit},
                )
                resp.raise_for_status()
                data = resp.json()

            tweets = data if isinstance(data, list) else data.get("tweets", [])
            return [
                {
                    "text": t.get("text", t.get("content", "")),
                    "likes": t.get("likes", t.get("favorite_count", 0)),
                    "retweets": t.get("retweets", t.get("retweet_count", 0)),
                    "created_at": t.get("created_at", ""),
                }
                for t in tweets[:limit]
            ]
        except Exception as e:
            logger.warning("Twitter scraping backend failed: %s", e)
            return []


class OfficialBackend:
    """Fetches tweets via X API v2 with Bearer token."""

    def __init__(self, bearer_token: str) -> None:
        self._token = bearer_token

    def search(self, query: str, limit: int = 20) -> list[dict]:
        try:
            with httpx.Client(timeout=_TIMEOUT) as client:
                resp = client.get(
                    "https://api.twitter.com/2/tweets/search/recent",
                    headers={"Authorization": f"Bearer {self._token}"},
                    params={
                        "query": f"{query} -is:retweet lang:en",
                        "max_results": min(limit, 100),
                        "tweet.fields": "created_at,public_metrics",
                    },
                )
                resp.raise_for_status()
                data = resp.json()

            tweets = []
            for t in data.get("data", []):
                metrics = t.get("public_metrics", {})
                tweets.append({
                    "text": t.get("text", ""),
                    "likes": metrics.get("like_count", 0),
                    "retweets": metrics.get("retweet_count", 0),
                    "created_at": t.get("created_at", ""),
                })
            return tweets
        except Exception as e:
            logger.warning("Twitter official API failed: %s", e)
            return []


def _classify_sentiment(text: str) -> str:
    """Simple keyword-based sentiment classification."""
    text_lower = text.lower()
    bullish_words = ["moon", "bullish", "pump", "buy", "long", "breakout", "ath", "rally", "gains"]
    bearish_words = ["dump", "bearish", "crash", "sell", "short", "rug", "scam", "dead", "rekt"]

    bull_score = sum(1 for w in bullish_words if w in text_lower)
    bear_score = sum(1 for w in bearish_words if w in text_lower)

    if bull_score > bear_score:
        return "bullish"
    elif bear_score > bull_score:
        return "bearish"
    return "neutral"


def get_twitter_sentiment(
    token: str = "SOL",
    bearer_token: str = "",
    scrape_url: str = "",
) -> dict:
    """Fetch and analyze Twitter/X sentiment for a token.

    Auto-selects backend:
    - bearer_token set → official API
    - scrape_url set → scraping proxy
    - neither → returns stub with note
    """
    query = f"${token} OR #solana" if token.upper() == "SOL" else f"${token}"

    # Select backend
    tweets: list[dict] = []
    backend_used = "none"

    if bearer_token:
        backend_used = "official_api"
        tweets = OfficialBackend(bearer_token).search(query)
    elif scrape_url:
        backend_used = "scraping_proxy"
        tweets = ScrapingBackend(scrape_url).search(query)
    else:
        return {
            "source": "twitter",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "backend": "none",
            "tweets": [],
            "sentiment_ratio": {"bullish": 0, "bearish": 0, "neutral": 0},
            "volume": 0,
            "note": "No Twitter backend configured. Set CA_TWITTER_BEARER_TOKEN or CA_TWITTER_SCRAPE_URL.",
        }

    if not tweets:
        return {
            "source": "twitter",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "backend": backend_used,
            "tweets": [],
            "sentiment_ratio": {"bullish": 0, "bearish": 0, "neutral": 0},
            "volume": 0,
            "note": f"No tweets returned from {backend_used}",
        }

    # Classify sentiment
    sentiments = [_classify_sentiment(t["text"]) for t in tweets]
    total = len(sentiments)
    ratio = {
        "bullish": round(sentiments.count("bullish") / total, 3),
        "bearish": round(sentiments.count("bearish") / total, 3),
        "neutral": round(sentiments.count("neutral") / total, 3),
    }

    # Top tweets by engagement
    tweets.sort(key=lambda t: t.get("likes", 0) + t.get("retweets", 0), reverse=True)

    return {
        "source": "twitter",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "backend": backend_used,
        "tweets": tweets[:10],
        "sentiment_ratio": ratio,
        "volume": total,
    }
