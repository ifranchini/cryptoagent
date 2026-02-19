"""CryptoPanic RSS news provider — fetches crypto headlines without API key."""

from __future__ import annotations

import logging
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

import httpx

logger = logging.getLogger(__name__)

_RSS_URL = "https://cryptopanic.com/news/rss/"
_TIMEOUT = 10
_HEADERS = {
    "User-Agent": "CryptoAgent/0.3.0 (+https://github.com/cryptoagent)",
}


def _sanitize_xml(xml_text: str) -> str:
    """Strip HTML tags and unescaped ampersands that break XML parsing."""
    # Remove HTML tags embedded in RSS content (e.g., <img>, <br>)
    cleaned = re.sub(r"<!\[CDATA\[.*?\]\]>", "", xml_text, flags=re.DOTALL)
    # Fix bare ampersands that aren't already entities
    cleaned = re.sub(r"&(?!amp;|lt;|gt;|quot;|apos;|#)", "&amp;", cleaned)
    return cleaned


def _parse_rss(xml_text: str) -> list[dict]:
    """Parse RSS XML and extract items. Tolerant of malformed feeds."""
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        # Retry after sanitizing common RSS issues
        root = ET.fromstring(_sanitize_xml(xml_text))

    items: list[dict] = []

    for item in root.iter("item"):
        title_el = item.find("title")
        link_el = item.find("link")
        pub_date_el = item.find("pubDate")

        if title_el is None or title_el.text is None:
            continue

        items.append({
            "title": title_el.text.strip(),
            "link": link_el.text.strip() if link_el is not None and link_el.text else "",
            "pub_date": pub_date_el.text.strip() if pub_date_el is not None and pub_date_el.text else "",
        })

    return items


def _matches_token(title: str, token: str) -> bool:
    """Check if a headline mentions the token (case-insensitive)."""
    title_lower = title.lower()
    token_lower = token.lower()

    # Token symbol match (e.g., "SOL")
    if f" {token_lower} " in f" {title_lower} ":
        return True

    # Common full-name mappings
    token_names: dict[str, list[str]] = {
        "sol": ["solana"],
        "btc": ["bitcoin"],
        "eth": ["ethereum"],
        "bnb": ["binance"],
        "xrp": ["ripple"],
        "ada": ["cardano"],
        "avax": ["avalanche"],
        "dot": ["polkadot"],
        "link": ["chainlink"],
        "arb": ["arbitrum"],
    }
    for name in token_names.get(token_lower, []):
        if name in title_lower:
            return True

    return False


def get_crypto_news(token: str, max_headlines: int = 10) -> dict:
    """Fetch crypto news from CryptoPanic RSS, optionally filtered by token.

    Args:
        token: Token symbol to filter headlines (e.g., "SOL").
        max_headlines: Maximum number of headlines to return.

    Returns:
        Dict with source, headlines list, and total_count.
    """
    try:
        resp = httpx.get(_RSS_URL, headers=_HEADERS, timeout=_TIMEOUT)
        resp.raise_for_status()

        all_items = _parse_rss(resp.text)

        # Filter by token mention
        filtered = [item for item in all_items if _matches_token(item["title"], token)]

        # If no token-specific news, return all headlines
        headlines = filtered[:max_headlines] if filtered else all_items[:max_headlines]
        filtered_only = bool(filtered)

        return {
            "source": "cryptopanic",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "token_filter": token.upper(),
            "token_specific": filtered_only,
            "headlines": headlines,
            "total_count": len(filtered) if filtered_only else len(all_items),
        }
    except Exception as e:
        logger.warning("CryptoPanic RSS fetch failed: %s", e)
        return {
            "source": "error",
            "message": str(e),
            "headlines": [],
            "total_count": 0,
        }
