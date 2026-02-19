"""Brain Agent — the core reasoning engine that makes trading decisions."""

from __future__ import annotations

import json
import logging

from cryptoagent.config import AgentConfig
from cryptoagent.graph.state import AgentState
from cryptoagent.llm.client import call_llm_json

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
You are an expert trading strategist and risk manager. You receive a research report \
(factual market analysis) and a sentiment report (social/news signals). Your job is to \
synthesize all evidence and make a trading decision.

## Decision Framework

1. **Identify Market Regime**: Determine if we're in a bull, bear, or sideways market based on \
the technical data and price action described in the research report.

2. **Weight Signals by Regime**:
   - In BEARISH or UNCERTAIN regimes: weight [FACT] signals 70-80%, [SUBJECTIVE/INFERENCE] 20-30%
   - In BULLISH regimes: weight [FACT] signals 50-60%, [SUBJECTIVE/INFERENCE] 40-50%
   - This reflects that narrative/sentiment matters more in bull markets, but hard data dominates in bears.

3. **Risk Assessment**: Consider current portfolio exposure, volatility (ATR), and your confidence level.

4. **Decision Output**: You MUST respond with a JSON object containing exactly these fields:
   - "action": one of "BUY", "SELL", "HOLD"
   - "asset": the token symbol (e.g., "SOL")
   - "size_pct": percentage of available capital to allocate (0-100, e.g., 10 means 10%)
   - "stop_loss_pct": stop loss as percentage below entry (e.g., 5 means 5% below)
   - "take_profit_pct": take profit as percentage above entry (e.g., 10 means 10% above)
   - "confidence": your confidence in this decision (1-10)
   - "regime": one of "bull", "bear", "sideways"
   - "rationale": 2-3 sentence explanation of your reasoning

For HOLD decisions, set size_pct to 0.
"""


def _build_user_prompt(
    token: str,
    research_report: str,
    sentiment_report: str,
    portfolio_state: dict,
    market_data: dict,
    reflection_memory: list[str],
) -> str:
    portfolio_str = json.dumps(portfolio_state, indent=2, default=str)
    memory_str = "\n".join(reflection_memory[-5:]) if reflection_memory else "No prior decisions."

    price_info = ""
    if market_data:
        price_info = (
            f"Current price: ${market_data.get('current_price', 'N/A')}\n"
            f"24h change: {market_data.get('price_change_24h_pct', 'N/A')}%"
        )

    return f"""\
## Target Asset: {token}
{price_info}

## Research Report
{research_report}

## Sentiment Report
{sentiment_report}

## Current Portfolio
{portfolio_str}

## Recent Decision History
{memory_str}

Based on all the above evidence, make your trading decision.
"""


def brain_node(state: AgentState) -> dict:
    """LangGraph node: Brain Agent.

    Synthesizes research + sentiment reports and makes a structured trading decision.
    """
    agent_config = AgentConfig()
    token = state["token"]

    logger.info("[Brain Agent] Reasoning about %s", token)

    user_prompt = _build_user_prompt(
        token=token,
        research_report=state.get("research_report", "No research report available."),
        sentiment_report=state.get("sentiment_report", "No sentiment report available."),
        portfolio_state=state.get("portfolio_state", {}),
        market_data=state.get("market_data", {}),
        reflection_memory=state.get("reflection_memory", []),
    )

    logger.info("[Brain Agent] Calling LLM: %s", agent_config.brain_model)
    decision = call_llm_json(
        model=agent_config.brain_model,
        system=SYSTEM_PROMPT,
        user=user_prompt,
    )

    # Validate required fields
    required = ["action", "asset", "size_pct", "confidence", "regime", "rationale"]
    for field in required:
        if field not in decision:
            decision[field] = {
                "action": "HOLD",
                "asset": token,
                "size_pct": 0,
                "confidence": 1,
                "regime": "sideways",
                "rationale": "Missing field, defaulting to HOLD.",
            }.get(field)

    # Clamp values
    decision["size_pct"] = max(0, min(100, float(decision.get("size_pct", 0))))
    decision["confidence"] = max(1, min(10, int(decision.get("confidence", 5))))

    decision_str = json.dumps(decision, indent=2)
    logger.info("[Brain Agent] Decision: %s", decision.get("action"))

    return {"brain_decision": decision_str}
