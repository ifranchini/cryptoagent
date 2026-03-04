"""Shared fixtures for CryptoAgent tests."""

from __future__ import annotations

import json
from unittest.mock import patch

import pytest

from cryptoagent.persistence.database import Database


@pytest.fixture
def in_memory_db() -> Database:
    """SQLite in-memory database with schema initialized."""
    db = Database(":memory:")
    _ = db.conn  # triggers schema creation
    return db


@pytest.fixture
def sample_portfolio() -> dict:
    """Realistic portfolio state for testing."""
    return {
        "cash": 5000.0,
        "holdings": {"SOL": 10.0},
        "net_worth": 6500.0,
        "trade_history": [],
    }


@pytest.fixture
def sample_market_data() -> dict:
    """Market data snapshot with indicators."""
    return {
        "current_price": 150.0,
        "volume_24h": 1_200_000_000.0,
        "price_vs_sma20": "above",
        "price_vs_sma50": "above",
        "indicators": {
            "rsi_14": 55.0,
            "macd_histogram": 1.2,
            "sma_20": 145.0,
            "sma_50": 140.0,
            "bb_upper": 160.0,
            "bb_lower": 130.0,
            "atr_14": 5.0,
        },
    }


@pytest.fixture
def sample_onchain_data() -> dict:
    """On-chain data with DeFiLlama + Solana network info."""
    return {
        "defillama": {
            "solana_tvl_change_7d": 5.2,
            "total_dex_volume_change_7d": 12.0,
        },
        "solana_network": {
            "whale_activity": {
                "whale_activity_level": "high",
            },
        },
    }


@pytest.fixture
def sample_agent_state(
    sample_market_data: dict,
    sample_onchain_data: dict,
) -> dict:
    """Full AgentState-like dict combining all data sources."""
    brain = {
        "action": "BUY",
        "asset": "SOL",
        "size_pct": 15,
        "stop_loss_pct": 5,
        "take_profit_pct": 10,
        "confidence": 7,
        "regime": "bull",
        "rationale": "Strong technicals with on-chain confirmation.",
    }
    return {
        "token": "SOL",
        "market_data": sample_market_data,
        "onchain_data": sample_onchain_data,
        "sentiment_report": "Community sentiment is bullish on SOL.",
        "fear_greed_index": 65,
        "macro_regime": "risk_on",
        "market_regime": "bull",
        "regime_confidence": 7,
        "brain_decision": json.dumps(brain),
    }


@pytest.fixture
def mock_llm():
    """Patch call_llm at common import sites to return a deterministic string."""
    with patch("cryptoagent.reflection.manager.call_llm") as m:
        m.return_value = "Mocked LLM reflection output."
        yield m
