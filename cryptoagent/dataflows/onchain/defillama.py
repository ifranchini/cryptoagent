"""DeFiLlama API — TVL, DEX volume, fees for Solana ecosystem."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

import httpx

logger = logging.getLogger(__name__)

_TIMEOUT = 10


def get_chain_tvl(base_url: str = "https://api.llama.fi") -> dict:
    """Fetch current TVL for Solana from DeFiLlama.

    Returns dict with tvl, tvl_change_1d, top protocols, or error dict.
    """
    try:
        with httpx.Client(timeout=_TIMEOUT) as client:
            # Current TVL for all chains
            resp = client.get(f"{base_url}/v2/chains")
            resp.raise_for_status()
            chains = resp.json()

            solana = next((c for c in chains if c.get("name", "").lower() == "solana"), None)
            if solana is None:
                return {"source": "error", "message": "Solana not found in chains list"}

            return {
                "source": "defillama",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "tvl": solana.get("tvl", 0),
                "token_symbol": solana.get("tokenSymbol", "SOL"),
            }
    except Exception as e:
        logger.warning("DeFiLlama chain TVL failed: %s", e)
        return {"source": "error", "message": str(e)}


def get_chain_tvl_history(base_url: str = "https://api.llama.fi") -> dict:
    """Fetch TVL history for Solana (last 7 data points)."""
    try:
        with httpx.Client(timeout=_TIMEOUT) as client:
            resp = client.get(f"{base_url}/v2/historicalChainTvl/Solana")
            resp.raise_for_status()
            data = resp.json()

            # Take last 7 entries
            recent = data[-7:] if len(data) >= 7 else data
            tvl_values = [entry.get("tvl", 0) for entry in recent]

            if len(tvl_values) >= 2:
                change_pct = ((tvl_values[-1] - tvl_values[0]) / tvl_values[0]) * 100 if tvl_values[0] else 0
            else:
                change_pct = 0

            return {
                "source": "defillama",
                "tvl_7d_history": tvl_values,
                "tvl_7d_change_pct": round(change_pct, 2),
            }
    except Exception as e:
        logger.warning("DeFiLlama TVL history failed: %s", e)
        return {"source": "error", "message": str(e)}


def get_dex_volume(base_url: str = "https://api.llama.fi") -> dict:
    """Fetch 24h DEX trading volume for Solana."""
    try:
        with httpx.Client(timeout=_TIMEOUT) as client:
            resp = client.get("https://api.llama.fi/overview/dexs/solana?excludeTotalDataChart=true&excludeTotalDataChartBreakdown=true&dataType=dailyVolume")
            resp.raise_for_status()
            data = resp.json()

            total_24h = data.get("total24h", 0)
            change_1d = data.get("change_1d", 0)

            # Top protocols by volume
            protocols = data.get("protocols", [])
            top_protocols = [
                {"name": p.get("name", ""), "volume_24h": p.get("total24h", 0)}
                for p in sorted(protocols, key=lambda x: x.get("total24h") or 0, reverse=True)[:5]
            ]

            return {
                "source": "defillama",
                "dex_volume_24h": total_24h,
                "dex_volume_change_1d_pct": change_1d,
                "top_dex_protocols": top_protocols,
            }
    except Exception as e:
        logger.warning("DeFiLlama DEX volume failed: %s", e)
        return {"source": "error", "message": str(e)}


def get_fees(base_url: str = "https://api.llama.fi") -> dict:
    """Fetch 24h fee data for Solana chain."""
    try:
        with httpx.Client(timeout=_TIMEOUT) as client:
            resp = client.get("https://api.llama.fi/overview/fees/solana?excludeTotalDataChart=true&excludeTotalDataChartBreakdown=true&dataType=dailyFees")
            resp.raise_for_status()
            data = resp.json()

            return {
                "source": "defillama",
                "fees_24h": data.get("total24h", 0),
                "fees_change_1d_pct": data.get("change_1d", 0),
            }
    except Exception as e:
        logger.warning("DeFiLlama fees failed: %s", e)
        return {"source": "error", "message": str(e)}


def get_all_onchain_data(base_url: str = "https://api.llama.fi") -> dict:
    """Aggregate all DeFiLlama data into a single dict."""
    tvl = get_chain_tvl(base_url)
    tvl_history = get_chain_tvl_history(base_url)
    dex = get_dex_volume(base_url)
    fees = get_fees(base_url)

    return {
        "source": "defillama",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tvl": tvl,
        "tvl_history": tvl_history,
        "dex_volume": dex,
        "fees": fees,
    }
