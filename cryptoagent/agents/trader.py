"""Trader Agent — validates and executes trade decisions."""

from __future__ import annotations

import json
import logging

from cryptoagent.config import AgentConfig
from cryptoagent.execution.router import execute_trade
from cryptoagent.graph.state import AgentState
from cryptoagent.llm.client import call_llm_json

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
You are a trade execution specialist. You receive a trading decision from the Brain agent \
and must validate whether it should be executed.

Your job:
1. Check if the trade makes sense given current portfolio and market conditions.
2. Flag any execution concerns (insufficient balance, excessive position size, etc.).
3. Decide whether to EXECUTE the trade as-is, MODIFY it (adjust size), or REJECT it.

Respond with a JSON object:
- "execute": true or false
- "modified_size_pct": adjusted size percentage (if modified, otherwise same as original)
- "order_type": "market" or "limit"
- "reason": brief explanation of your execution decision

If the Brain's action is HOLD, set execute to false with reason "HOLD — no trade needed".
"""


def _build_user_prompt(
    brain_decision: dict,
    portfolio_state: dict,
    market_data: dict,
) -> str:
    return f"""\
## Brain's Trading Decision
{json.dumps(brain_decision, indent=2)}

## Current Portfolio
{json.dumps(portfolio_state, indent=2, default=str)}

## Current Market
Price: ${market_data.get('current_price', 'N/A')}
24h Volume: {market_data.get('volume_24h', 'N/A')}

Validate and decide on execution.
"""


def trader_node(state: AgentState) -> dict:
    """LangGraph node: Trader Agent.

    Validates Brain's decision and executes via paper/live trading.
    """
    agent_config = AgentConfig()

    brain_decision_str = state.get("brain_decision", "{}")
    try:
        brain_decision = json.loads(brain_decision_str)
    except json.JSONDecodeError:
        brain_decision = {"action": "HOLD", "rationale": "Could not parse brain decision."}

    portfolio_state = state.get("portfolio_state", {})
    market_data = state.get("market_data", {})

    logger.info("[Trader Agent] Evaluating decision: %s", brain_decision.get("action"))

    # For HOLD, skip LLM call
    if brain_decision.get("action") == "HOLD":
        result = {
            "executed": False,
            "reason": "HOLD — no trade needed",
            "brain_decision": brain_decision,
        }
        return {"trade_result": json.dumps(result, indent=2)}

    # Validate via LLM
    user_prompt = _build_user_prompt(brain_decision, portfolio_state, market_data)

    logger.info("[Trader Agent] Calling LLM: %s", agent_config.trader_model)
    validation = call_llm_json(
        model=agent_config.trader_model,
        system=SYSTEM_PROMPT,
        user=user_prompt,
    )

    should_execute = validation.get("execute", False)
    final_size_pct = float(validation.get("modified_size_pct", brain_decision.get("size_pct", 0)))

    # Cap position size
    max_pct = agent_config.max_position_pct * 100
    if final_size_pct > max_pct:
        logger.warning("[Trader Agent] Size %s%% exceeds max %s%%, capping", final_size_pct, max_pct)
        final_size_pct = max_pct

    if should_execute and final_size_pct > 0:
        # Execute trade
        execution_result = execute_trade(
            action=brain_decision["action"],
            token=brain_decision.get("asset", state.get("token", "SOL")),
            size_pct=final_size_pct,
            portfolio_state=portfolio_state,
            current_price=market_data.get("current_price", 0),
            fee_pct=agent_config.trading_fee_pct,
            mode=agent_config.execution_mode,
        )
        result = {
            "executed": True,
            "execution": execution_result,
            "validation": validation,
            "brain_decision": brain_decision,
        }
    else:
        result = {
            "executed": False,
            "reason": validation.get("reason", "Trade rejected by Trader Agent"),
            "validation": validation,
            "brain_decision": brain_decision,
        }

    result_str = json.dumps(result, indent=2, default=str)
    logger.info("[Trader Agent] Result: executed=%s", result.get("executed"))

    return {
        "trade_result": result_str,
        "portfolio_state": result.get("execution", {}).get("updated_portfolio", portfolio_state),
    }
