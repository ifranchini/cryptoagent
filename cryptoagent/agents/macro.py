"""Macro Analyst Agent — assesses macroeconomic conditions for crypto markets."""

from __future__ import annotations

import json
import logging

from cryptoagent.config import AgentConfig
from cryptoagent.dataflows.aggregator import DataAggregator
from cryptoagent.graph.state import AgentState
from cryptoagent.llm.client import call_llm

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
You are a macroeconomic analyst specializing in crypto market impact. Your job is to \
assess the macro environment and determine how it affects risk appetite for crypto assets.

Rules:
1. Label each finding as [FACT] (data-driven, verifiable) or [INFERENCE] (your interpretation).
2. Structure your report: Monetary Policy, Liquidity Conditions, Yield Curve, Macro Regime Assessment.
3. Note correlation direction: e.g., "Expanding M2 historically bullish for risk assets."
4. Keep it under 300 words.
5. End with a regime recommendation: risk-on / risk-off / neutral.
"""


def _build_user_prompt(macro_data: dict, macro_regime: dict) -> str:
    regime_str = macro_regime.get("macro_regime", "unknown")
    confidence = macro_regime.get("confidence", 0)
    signals = json.dumps(macro_regime.get("signals", {}), indent=2)

    return f"""\
Analyze the following macroeconomic data and produce your macro report.

## FRED Macro Data
{json.dumps(macro_data, indent=2, default=str)}

## Pre-Computed Macro Regime
Regime: {regime_str} (confidence: {confidence}/10)
Signals:
{signals}

Assess the macro environment's impact on crypto markets.
"""


def macro_node(state: AgentState) -> dict:
    """LangGraph node: Macro Analyst Agent.

    Fetches macro data from FRED, classifies regime, sends to LLM for analysis.
    """
    agent_config = AgentConfig()
    aggregator = DataAggregator(exchange=agent_config.exchange, config=agent_config)

    logger.info("[Macro Agent] Collecting macro data")

    macro_result = aggregator.get_macro_data()
    fred_data = macro_result.get("fred", macro_result)
    macro_regime = macro_result.get("macro_regime", {
        "macro_regime": "unknown",
        "confidence": 0,
        "signals": {},
    })

    user_prompt = _build_user_prompt(fred_data, macro_regime)

    logger.info("[Macro Agent] Calling LLM: %s", agent_config.macro_model)
    report = call_llm(
        model=agent_config.macro_model,
        system=SYSTEM_PROMPT,
        user=user_prompt,
    )

    regime_label = macro_regime.get("macro_regime", "unknown")
    logger.info(
        "[Macro Agent] Report generated (%d chars), regime: %s",
        len(report),
        regime_label,
    )

    return {
        "macro_report": report,
        "macro_regime": regime_label,
    }
