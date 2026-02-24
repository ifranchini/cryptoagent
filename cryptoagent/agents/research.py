"""Research Agent — collects and synthesizes market data into a research report."""

from __future__ import annotations

import json
import logging

from cryptoagent.config import AgentConfig
from cryptoagent.dataflows.aggregator import DataAggregator
from cryptoagent.graph.state import AgentState
from cryptoagent.llm.client import call_llm

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
You are a senior crypto/financial research analyst. Your job is to produce a concise, \
actionable research summary based on raw market data, on-chain metrics, macro indicators, \
and protocol fundamentals.

Rules:
1. Label each finding as [FACT] (data-driven, verifiable) or [INFERENCE] (your interpretation).
2. Structure your report with these sections: Price Action, Technical Signals, On-Chain Health, \
Protocol Fundamentals, Macro Environment.
3. End with a "Key Signals" section listing the 3-5 most important signals for a trading decision.
4. Be specific with numbers. Don't be vague.
5. Keep it under 600 words.
"""


def _build_user_prompt(
    token: str,
    market_data: dict,
    onchain_data: dict,
    macro_data: dict,
    protocol_data: dict,
) -> str:
    prompt = f"""\
Analyze the following data for {token} and produce your research report.

## Market Data
{json.dumps(market_data, indent=2, default=str)}

## On-Chain Data
{json.dumps(onchain_data, indent=2, default=str)}

## Macro Environment
{json.dumps(macro_data, indent=2, default=str)}
"""
    if protocol_data and protocol_data.get("source") != "stub":
        prompt += f"""
## Protocol Fundamentals
{json.dumps(protocol_data, indent=2, default=str)}
"""
    else:
        prompt += "\n## Protocol Fundamentals\nNot available for this cycle.\n"
    return prompt


def research_node(state: AgentState) -> dict:
    """LangGraph node: Research Agent.

    Fetches market + on-chain + macro data, sends to LLM for analysis.
    """
    agent_config = AgentConfig()
    token = state["token"]
    aggregator = DataAggregator(exchange=agent_config.exchange)

    logger.info("[Research Agent] Collecting data for %s", token)

    market_data = aggregator.get_market_data(token)
    onchain_data = aggregator.get_onchain_data(token)
    macro_data = aggregator.get_macro_data()
    protocol_data = aggregator.get_protocol_data(token)

    user_prompt = _build_user_prompt(
        token,
        market_data,
        onchain_data,
        macro_data,
        protocol_data,
    )

    logger.info("[Research Agent] Calling LLM: %s", agent_config.research_model)
    report = call_llm(
        model=agent_config.research_model,
        system=SYSTEM_PROMPT,
        user=user_prompt,
    )

    logger.info("[Research Agent] Report generated (%d chars)", len(report))

    return {
        "research_report": report,
        "market_data": market_data,
        "onchain_data": onchain_data,
        "protocol_data": protocol_data,
    }
