"""Sentiment Agent — analyzes social signals and news for market sentiment."""

from __future__ import annotations

import json
import logging

from cryptoagent.config import AgentConfig
from cryptoagent.dataflows.aggregator import DataAggregator
from cryptoagent.graph.state import AgentState
from cryptoagent.llm.client import call_llm

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
You are a crypto/financial sentiment analyst. Your job is to analyze social media signals, \
news, and crowd sentiment to produce a sentiment report.

Rules:
1. Separate [FACTUAL] observations (e.g., "Fear & Greed Index is 55") from \
[SUBJECTIVE] interpretations (e.g., "Market mood feels cautious").
2. Assess overall sentiment direction: Strong Bearish / Bearish / Neutral / Bullish / Strong Bullish.
3. Rate sentiment intensity from 1 (very weak signal) to 10 (very strong signal).
4. Note any divergences between different sentiment sources.
5. Keep it under 300 words.
"""


def _build_user_prompt(token: str, sentiment_data: dict) -> str:
    return f"""\
Analyze the following sentiment data for {token} and produce your sentiment report.

## Sentiment Data
{json.dumps(sentiment_data, indent=2, default=str)}

Produce a concise sentiment report with direction, intensity, and key observations.
"""


def sentiment_node(state: AgentState) -> dict:
    """LangGraph node: Sentiment Agent.

    Fetches social/news sentiment data, sends to LLM for analysis.
    """
    agent_config = AgentConfig()
    token = state["token"]
    aggregator = DataAggregator(exchange=agent_config.exchange)

    logger.info("[Sentiment Agent] Collecting sentiment data for %s", token)

    sentiment_data = aggregator.get_sentiment_data(token)

    user_prompt = _build_user_prompt(token, sentiment_data)

    logger.info("[Sentiment Agent] Calling LLM: %s", agent_config.sentiment_model)
    report = call_llm(
        model=agent_config.sentiment_model,
        system=SYSTEM_PROMPT,
        user=user_prompt,
    )

    logger.info("[Sentiment Agent] Report generated (%d chars)", len(report))

    return {"sentiment_report": report}
