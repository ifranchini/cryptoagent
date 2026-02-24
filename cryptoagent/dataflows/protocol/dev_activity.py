"""GitHub API — developer activity metrics for crypto projects."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

import httpx

logger = logging.getLogger(__name__)

_TIMEOUT = 10
_GITHUB_API = "https://api.github.com"

# Maps token symbols to their primary GitHub repo (owner/repo).
_TOKEN_REPOS: dict[str, str] = {
    "SOL": "anza-xyz/agave",
    "ETH": "ethereum/go-ethereum",
    "BTC": "bitcoin/bitcoin",
    "ARB": "OffchainLabs/nitro",
    "OP": "ethereum-optimism/optimism",
    "AAVE": "aave/aave-v3-core",
    "UNI": "Uniswap/v3-core",
    "LINK": "smartcontractkit/chainlink",
    "MKR": "makerdao/dss",
    "PENDLE": "pendle-finance/pendle-core-v2-public",
    "GMX": "gmx-io/gmx-synthetics",
    "DYDX": "dydxprotocol/v4-chain",
    "INJ": "InjectiveLabs/injective-core",
    "TIA": "celestiaorg/celestia-node",
    "SNX": "Synthetixio/synthetix-v3",
}


def _classify_health(commits_4w: int) -> str:
    """Classify dev activity level based on 4-week commit count."""
    if commits_4w >= 20:
        return "active"
    if commits_4w >= 5:
        return "moderate"
    return "stale"


def get_dev_activity(token: str) -> dict:
    """Fetch GitHub development metrics for a token's primary repository.

    Returns commit activity (last 4 weeks), contributor count,
    stars, forks, and a health classification.

    Uses unauthenticated GitHub API (60 requests/hour limit).
    """
    token_upper = token.upper()
    repo_path = _TOKEN_REPOS.get(token_upper)

    if not repo_path:
        return {
            "source": "github",
            "token": token_upper,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "note": f"No GitHub repo configured for {token_upper}",
            "health": "unknown",
        }

    try:
        headers = {"Accept": "application/vnd.github.v3+json"}

        with httpx.Client(timeout=_TIMEOUT, headers=headers) as client:
            # Repo metadata (stars, forks, last push)
            repo_resp = client.get(f"{_GITHUB_API}/repos/{repo_path}")
            repo_resp.raise_for_status()
            repo_data = repo_resp.json()

            # Weekly commit activity (last 52 weeks)
            commit_resp = client.get(
                f"{_GITHUB_API}/repos/{repo_path}/stats/commit_activity"
            )

            commits_4w = 0
            weekly_breakdown: list[int] = []
            if commit_resp.status_code == 200:
                weeks = commit_resp.json()
                if isinstance(weeks, list) and len(weeks) >= 4:
                    recent_4 = weeks[-4:]
                    weekly_breakdown = [w.get("total", 0) for w in recent_4]
                    commits_4w = sum(weekly_breakdown)
            elif commit_resp.status_code == 202:
                # GitHub returns 202 when stats are being computed
                logger.info(
                    "GitHub stats being computed for %s, using repo metadata", repo_path
                )

        health = _classify_health(commits_4w)

        return {
            "source": "github",
            "token": token_upper,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "repo": repo_path,
            "stars": repo_data.get("stargazers_count", 0),
            "forks": repo_data.get("forks_count", 0),
            "open_issues": repo_data.get("open_issues_count", 0),
            "last_push": repo_data.get("pushed_at", ""),
            "commits_last_4_weeks": commits_4w,
            "weekly_commits": weekly_breakdown,
            "health": health,
        }
    except httpx.HTTPStatusError as e:
        logger.warning("GitHub API error for %s: %s", repo_path, e.response.status_code)
        return {
            "source": "error",
            "token": token_upper,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "message": f"HTTP {e.response.status_code}",
            "health": "unknown",
        }
    except Exception as e:
        logger.warning("GitHub dev activity failed for %s: %s", token_upper, e)
        return {
            "source": "error",
            "token": token_upper,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "message": str(e),
            "health": "unknown",
        }
