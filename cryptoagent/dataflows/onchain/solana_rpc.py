"""Solana RPC — network TPS and whale activity via public endpoints."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

import httpx

logger = logging.getLogger(__name__)

_TIMEOUT = 10

# Known high-value Solana addresses for whale tracking
_WHALE_ADDRESSES = [
    "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",  # Major SOL holder
]


def _rpc_call(url: str, method: str, params: list | None = None) -> dict:
    """Make a JSON-RPC call to the Solana RPC endpoint."""
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": method,
        "params": params or [],
    }
    with httpx.Client(timeout=_TIMEOUT) as client:
        resp = client.post(url, json=payload)
        resp.raise_for_status()
        return resp.json()


def get_network_tps(rpc_url: str = "https://api.mainnet-beta.solana.com") -> dict:
    """Fetch recent network TPS from performance samples.

    Uses getRecentPerformanceSamples to compute average TPS.
    """
    try:
        result = _rpc_call(rpc_url, "getRecentPerformanceSamples", [5])
        samples = result.get("result", [])

        if not samples:
            return {"source": "error", "message": "No performance samples returned"}

        tps_values = []
        for s in samples:
            num_txs = s.get("numTransactions", 0)
            slot_time = s.get("samplePeriodSecs", 60)
            if slot_time > 0:
                tps_values.append(num_txs / slot_time)

        avg_tps = sum(tps_values) / len(tps_values) if tps_values else 0

        return {
            "source": "solana_rpc",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "avg_tps": round(avg_tps, 0),
            "samples": len(samples),
            "tps_range": {
                "min": round(min(tps_values), 0) if tps_values else 0,
                "max": round(max(tps_values), 0) if tps_values else 0,
            },
        }
    except Exception as e:
        logger.warning("Solana RPC TPS failed: %s", e)
        return {"source": "error", "message": str(e)}


def get_whale_activity(
    rpc_url: str = "https://api.mainnet-beta.solana.com",
    addresses: list[str] | None = None,
) -> dict:
    """Check recent transaction activity for known whale addresses.

    Uses getSignaturesForAddress to detect recent large-scale activity.
    """
    addresses = addresses or _WHALE_ADDRESSES
    activity = []

    try:
        for addr in addresses[:3]:  # Limit to avoid rate limits
            result = _rpc_call(
                rpc_url,
                "getSignaturesForAddress",
                [addr, {"limit": 5}],
            )
            sigs = result.get("result", [])
            recent_count = len(sigs)

            if sigs:
                latest_slot = sigs[0].get("slot", 0)
            else:
                latest_slot = 0

            activity.append({
                "address": addr[:8] + "...",
                "recent_tx_count": recent_count,
                "latest_slot": latest_slot,
            })

        total_recent = sum(a["recent_tx_count"] for a in activity)
        whale_level = "high" if total_recent > 10 else "moderate" if total_recent > 3 else "low"

        return {
            "source": "solana_rpc",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "whale_activity_level": whale_level,
            "total_recent_txs": total_recent,
            "tracked_addresses": len(addresses),
            "details": activity,
        }
    except Exception as e:
        logger.warning("Solana RPC whale activity failed: %s", e)
        return {"source": "error", "message": str(e)}


def get_solana_network_data(rpc_url: str = "https://api.mainnet-beta.solana.com") -> dict:
    """Aggregate all Solana RPC data."""
    tps = get_network_tps(rpc_url)
    whales = get_whale_activity(rpc_url)

    return {
        "source": "solana_rpc",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "network_tps": tps,
        "whale_activity": whales,
    }
