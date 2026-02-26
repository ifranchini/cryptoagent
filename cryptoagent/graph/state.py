"""LangGraph state schema for the trading pipeline."""

from __future__ import annotations

from typing import TypedDict


class PortfolioState(TypedDict, total=False):
    """Current portfolio snapshot."""

    cash: float
    holdings: dict[str, float]  # token -> quantity
    net_worth: float
    trade_history: list[dict]


class AgentState(TypedDict, total=False):
    """Shared state flowing through the LangGraph pipeline.

    Each agent reads what it needs and writes its output key.
    LangGraph handles fan-out (Research + Sentiment in parallel)
    and fan-in (both must complete before Brain runs).
    """

    # Target
    token: str
    asset_type: str  # "crypto" | "equity"
    timestamp: str

    # Agent outputs
    research_report: str
    sentiment_report: str
    brain_decision: str  # JSON string: action, size, SL, TP, reasoning
    trade_result: str

    # Context
    portfolio_state: PortfolioState
    market_data: dict  # Raw OHLCV + indicators
    reflection_memory: list[str]  # Past decisions + outcomes

    # Phase 2 additions
    onchain_data: dict  # TVL, DEX volume, whale activity
    market_regime: str  # "bull" | "bear" | "sideways"
    regime_confidence: int  # 1-10
    fear_greed_index: int  # 0-100
    risk_verdict: str  # "proceed" | "halt" | "reduce"
    cross_trial_reflections: list[str]  # Level 2 reflections from prior runs

    # Phase 3 additions
    macro_report: str  # Macro Analyst agent output
    macro_regime: str  # "risk_on" | "risk_off" | "neutral"
    news_data: dict  # CryptoPanic headlines
    protocol_data: dict  # Protocol TVL, fees, governance, dev activity

    # Phase 4 additions
    signal_report: str  # Signal accuracy report for Brain context
