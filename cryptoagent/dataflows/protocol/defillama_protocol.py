"""DeFiLlama API — protocol-level TVL, fees, and revenue."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

import httpx

logger = logging.getLogger(__name__)

_TIMEOUT = 10

# Maps token symbols to their primary DeFiLlama protocol slugs.
# Each token may have multiple key protocols; we track the most representative ones.
_TOKEN_PROTOCOL_SLUGS: dict[str, list[str]] = {
    "SOL": ["raydium", "jupiter", "marinade-finance", "jito"],
    "ETH": ["lido", "aave", "uniswap", "eigenlayer"],
    "BTC": ["babylon-finance"],
    "ARB": ["gmx", "aave", "uniswap"],
    "OP": ["velodrome-v2", "aave", "synthetix"],
    "AAVE": ["aave"],
    "UNI": ["uniswap"],
    "LINK": ["chainlink"],
    "MKR": ["makerdao"],
    "PENDLE": ["pendle"],
    "GMX": ["gmx"],
    "DYDX": ["dydx"],
    "INJ": ["injective"],
    "TIA": ["celestia"],
    "SNX": ["synthetix"],
}


def get_protocol_tvl(
    slug: str,
    base_url: str = "https://api.llama.fi",
) -> dict:
    """Fetch protocol-level TVL and TVL history from DeFiLlama.

    Returns current TVL, 7d change, and chain breakdown.
    """
    try:
        with httpx.Client(timeout=_TIMEOUT) as client:
            resp = client.get(f"{base_url}/protocol/{slug}")
            resp.raise_for_status()
            data = resp.json()

            current_tvl = data.get("currentChainTvls", {})
            total_tvl = sum(
                v
                for k, v in current_tvl.items()
                if not k.endswith("-staking") and not k.endswith("-borrowed")
            )

            # 7d TVL change from history
            tvl_history = data.get("tvl", [])
            tvl_7d_change_pct = 0.0
            if len(tvl_history) >= 7:
                old = tvl_history[-7].get("totalLiquidityUSD", 0)
                new = tvl_history[-1].get("totalLiquidityUSD", 0)
                if old > 0:
                    tvl_7d_change_pct = round(((new - old) / old) * 100, 2)

            return {
                "slug": slug,
                "name": data.get("name", slug),
                "tvl": round(total_tvl, 2),
                "tvl_7d_change_pct": tvl_7d_change_pct,
                "category": data.get("category", "unknown"),
                "chains": list(data.get("chains", [])),
            }
    except httpx.HTTPStatusError as e:
        logger.warning(
            "DeFiLlama protocol %s HTTP error: %s", slug, e.response.status_code
        )
        return {"slug": slug, "source": "error", "message": str(e)}
    except Exception as e:
        logger.warning("DeFiLlama protocol %s failed: %s", slug, e)
        return {"slug": slug, "source": "error", "message": str(e)}


def get_protocol_fees(
    slug: str,
    base_url: str = "https://api.llama.fi",
) -> dict:
    """Fetch 24h and 30d fees/revenue for a protocol from DeFiLlama."""
    try:
        with httpx.Client(timeout=_TIMEOUT) as client:
            resp = client.get(f"{base_url}/summary/fees/{slug}?dataType=dailyFees")
            resp.raise_for_status()
            data = resp.json()

            return {
                "slug": slug,
                "fees_24h": data.get("total24h"),
                "fees_30d": data.get("total30d"),
                "revenue_24h": data.get("totalRevenue24h"),
            }
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return {"slug": slug, "fees_24h": None, "note": "No fee data available"}
        logger.warning("DeFiLlama fees %s HTTP error: %s", slug, e.response.status_code)
        return {"slug": slug, "source": "error", "message": str(e)}
    except Exception as e:
        logger.warning("DeFiLlama fees %s failed: %s", slug, e)
        return {"slug": slug, "source": "error", "message": str(e)}


def get_protocol_fundamentals(
    token: str,
    base_url: str = "https://api.llama.fi",
) -> dict:
    """Aggregate TVL and fee data for all protocols mapped to a token.

    Returns a combined report with per-protocol breakdown.
    """
    slugs = _TOKEN_PROTOCOL_SLUGS.get(token.upper(), [])
    if not slugs:
        return {
            "source": "defillama_protocol",
            "token": token.upper(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "note": f"No protocol mappings configured for {token.upper()}",
            "protocols": [],
        }

    protocols = []
    for slug in slugs:
        tvl_data = get_protocol_tvl(slug, base_url)
        fee_data = get_protocol_fees(slug, base_url)

        if tvl_data.get("source") == "error" and fee_data.get("source") == "error":
            continue

        entry: dict = {"slug": slug}
        if tvl_data.get("source") != "error":
            entry["name"] = tvl_data.get("name", slug)
            entry["tvl"] = tvl_data.get("tvl")
            entry["tvl_7d_change_pct"] = tvl_data.get("tvl_7d_change_pct")
            entry["category"] = tvl_data.get("category")
        if fee_data.get("source") != "error":
            entry["fees_24h"] = fee_data.get("fees_24h")
            entry["fees_30d"] = fee_data.get("fees_30d")
            entry["revenue_24h"] = fee_data.get("revenue_24h")

        protocols.append(entry)

    total_tvl = sum(p.get("tvl", 0) or 0 for p in protocols)

    return {
        "source": "defillama_protocol",
        "token": token.upper(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_ecosystem_tvl": round(total_tvl, 2),
        "protocol_count": len(protocols),
        "protocols": protocols,
    }
