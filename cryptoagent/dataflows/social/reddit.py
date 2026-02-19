"""Reddit JSON API — fetch hot posts from crypto subreddits."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

import httpx

logger = logging.getLogger(__name__)

_TIMEOUT = 10
_USER_AGENT = "CryptoAgent/0.2.0 (research bot)"


def fetch_subreddit_hot(
    subreddit: str,
    token_filter: str = "SOL",
    limit: int = 25,
) -> list[dict]:
    """Fetch hot posts from a subreddit via the public JSON API.

    Filters posts that mention the target token (case-insensitive).
    """
    url = f"https://www.reddit.com/r/{subreddit}/hot.json"
    headers = {"User-Agent": _USER_AGENT}
    params = {"limit": limit, "raw_json": 1}

    try:
        with httpx.Client(timeout=_TIMEOUT, follow_redirects=True) as client:
            resp = client.get(url, headers=headers, params=params)
            resp.raise_for_status()
            data = resp.json()

        posts = []
        token_lower = token_filter.lower()
        sol_keywords = [token_lower, "solana"] if token_lower == "sol" else [token_lower]

        for child in data.get("data", {}).get("children", []):
            post = child.get("data", {})
            title = post.get("title", "")
            selftext = post.get("selftext", "")
            combined = f"{title} {selftext}".lower()

            # For r/solana, include all posts; for others, filter by token mention
            if subreddit.lower() == "solana" or any(kw in combined for kw in sol_keywords):
                posts.append({
                    "title": title,
                    "score": post.get("score", 0),
                    "num_comments": post.get("num_comments", 0),
                    "created_utc": post.get("created_utc", 0),
                    "subreddit": subreddit,
                    "upvote_ratio": post.get("upvote_ratio", 0),
                })

        return posts

    except Exception as e:
        logger.warning("Reddit fetch for r/%s failed: %s", subreddit, e)
        return []


def get_reddit_sentiment(
    subreddits: list[str] | None = None,
    token: str = "SOL",
) -> dict:
    """Aggregate Reddit sentiment data from multiple subreddits.

    Returns structured dict with posts, volume, and overall tone assessment.
    """
    subreddits = subreddits or ["solana", "cryptocurrency"]
    all_posts: list[dict] = []

    for sub in subreddits:
        posts = fetch_subreddit_hot(sub, token_filter=token)
        all_posts.extend(posts)

    if not all_posts:
        return {
            "source": "reddit",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "posts": [],
            "volume": 0,
            "overall_tone": "no_data",
            "top_topics": [],
            "note": "No relevant posts found on Reddit",
        }

    # Sort by engagement (score + comments)
    all_posts.sort(key=lambda p: p["score"] + p["num_comments"], reverse=True)
    top_posts = all_posts[:10]

    # Simple tone assessment based on upvote ratios and engagement
    avg_upvote_ratio = sum(p["upvote_ratio"] for p in all_posts) / len(all_posts)
    total_score = sum(p["score"] for p in all_posts)
    avg_score = total_score / len(all_posts)

    if avg_upvote_ratio > 0.75 and avg_score > 50:
        tone = "bullish"
    elif avg_upvote_ratio > 0.65:
        tone = "slightly_bullish"
    elif avg_upvote_ratio < 0.45:
        tone = "bearish"
    elif avg_upvote_ratio < 0.55:
        tone = "slightly_bearish"
    else:
        tone = "neutral"

    return {
        "source": "reddit",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "posts": top_posts,
        "volume": len(all_posts),
        "overall_tone": tone,
        "avg_upvote_ratio": round(avg_upvote_ratio, 3),
        "total_engagement": total_score,
        "top_topics": [p["title"][:80] for p in top_posts[:5]],
    }
