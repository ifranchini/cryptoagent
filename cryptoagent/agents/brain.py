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
(factual market analysis), a sentiment report (social/news signals), on-chain data, and \
a pre-computed market regime classification. Your job is to synthesize all evidence and \
make a trading decision.

## Decision Framework

1. **Confirm/Override Market Regime**: A regime classifier has pre-computed a regime \
(bull/bear/sideways) with confidence. You may confirm or override it based on the full picture.

2. **Weight Signals by Regime**:
   - In BEARISH or UNCERTAIN regimes: weight [FACT] signals 70-80%, [SUBJECTIVE/INFERENCE] 20-30%
   - In BULLISH regimes: weight [FACT] signals 50-60%, [SUBJECTIVE/INFERENCE] 40-50%
   - This reflects that narrative/sentiment matters more in bull markets, but hard data dominates in bears.

3. **On-Chain Signals**: Incorporate TVL trends, DEX volume, whale activity, and network TPS \
as leading indicators. Rising TVL + DEX volume = bullish; declining = bearish.

4. **Protocol Fundamentals**: Evaluate protocol health from TVL, fee revenue, governance \
activity, and developer commits. Strong fundamentals (growing TVL, active dev, healthy \
governance) support higher conviction. Stale development or declining TVL is a red flag.

5. **Fear & Greed Context**: Use the Fear & Greed Index as a contrarian indicator at extremes \
(Extreme Fear = potential buy; Extreme Greed = potential sell) and as confirmation in the middle range.

6. **Cross-Trial Memory**: If cross-trial reflections are provided, incorporate lessons learned \
from prior trading sessions. Avoid repeating past mistakes.

7. **Risk Assessment**: Consider current portfolio exposure, volatility (ATR), and your confidence level.

8. **Macro Context**: Consider the macro regime (risk-on/risk-off) alongside market regime. \
Divergence between market and macro regimes signals caution.

9. **Signal Accuracy**: If a Signal Accuracy Report is provided, weight signals with higher \
historical accuracy more heavily in your analysis. Signals with low hit rates should be \
treated with skepticism. Pay attention to timeframe-specific accuracy — a signal reliable \
at 7d may not be useful for short-term decisions.

10. **Decision Output**: You MUST respond with a JSON object containing exactly these fields:
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
    onchain_data: dict | None = None,
    market_regime: str = "unknown",
    regime_confidence: int = 0,
    fear_greed_index: int = 50,
    cross_trial_reflections: list[str] | None = None,
    macro_report: str = "",
    macro_regime: str = "unknown",
    signal_report: str = "",
) -> str:
    portfolio_str = json.dumps(portfolio_state, indent=2, default=str)
    memory_str = (
        "\n".join(reflection_memory[-5:])
        if reflection_memory
        else "No prior decisions."
    )

    price_info = ""
    if market_data:
        price_info = (
            f"Current price: ${market_data.get('current_price', 'N/A')}\n"
            f"24h change: {market_data.get('price_change_24h_pct', 'N/A')}%"
        )

    # On-chain section
    onchain_section = ""
    if onchain_data and onchain_data.get("source") != "stub":
        onchain_section = (
            f"\n## On-Chain Data\n{json.dumps(onchain_data, indent=2, default=str)}\n"
        )
    else:
        onchain_section = "\n## On-Chain Data\nNot available for this cycle.\n"

    # Macro analysis section
    macro_section = ""
    if macro_report:
        macro_section = f"\n## Macro Analysis\n{macro_report}\n"

    # Regime section — both market and macro regimes
    regime_section = (
        f"\n## Market Context\n"
        f"Market Regime: {market_regime} (confidence: {regime_confidence}/10)\n"
        f"Macro Regime: {macro_regime}\n"
        f"Fear & Greed Index: {fear_greed_index}/100\n"
    )

    # Signal accuracy report
    signal_section = ""
    if signal_report:
        signal_section = f"\n## Signal Accuracy Report\n{signal_report}\n"

    # Cross-trial reflections
    cross_trial_str = ""
    if cross_trial_reflections:
        cross_trial_str = (
            "\n## Cross-Trial Reflections (Lessons from Prior Sessions)\n"
            + "\n".join(f"- {r}" for r in cross_trial_reflections)
            + "\n"
        )

    return f"""\
## Target Asset: {token}
{price_info}

## Research Report
{research_report}

## Sentiment Report
{sentiment_report}
{macro_section}{onchain_section}{regime_section}{signal_section}{cross_trial_str}
## Current Portfolio
{portfolio_str}

## Recent Decision History
{memory_str}

Based on all the above evidence, make your trading decision.
"""


def brain_node(state: AgentState) -> dict:
    """LangGraph node: Brain Agent.

    Synthesizes research + sentiment + on-chain + regime and makes a structured trading decision.
    """
    agent_config = AgentConfig()
    token = state["token"]

    logger.info("[Brain Agent] Reasoning about %s", token)

    user_prompt = _build_user_prompt(
        token=token,
        research_report=state.get("research_report", "No research report available."),
        sentiment_report=state.get(
            "sentiment_report", "No sentiment report available."
        ),
        portfolio_state=state.get("portfolio_state", {}),
        market_data=state.get("market_data", {}),
        reflection_memory=state.get("reflection_memory", []),
        onchain_data=state.get("onchain_data"),
        market_regime=state.get("market_regime", "unknown"),
        regime_confidence=state.get("regime_confidence", 0),
        fear_greed_index=state.get("fear_greed_index", 50),
        cross_trial_reflections=state.get("cross_trial_reflections"),
        macro_report=state.get("macro_report", ""),
        macro_regime=state.get("macro_regime", "unknown"),
        signal_report=state.get("signal_report", ""),
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
