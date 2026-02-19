"""LangGraph pipeline — wires the 4 agents into a parallel-then-sequential flow."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from langgraph.graph import END, START, StateGraph

from cryptoagent.agents.brain import brain_node
from cryptoagent.agents.research import research_node
from cryptoagent.agents.sentiment import sentiment_node
from cryptoagent.agents.trader import trader_node
from cryptoagent.config import AgentConfig
from cryptoagent.graph.state import AgentState

logger = logging.getLogger(__name__)


def build_graph() -> StateGraph:
    """Build the 4-agent trading pipeline.

    Flow:
        START ──┬── research ──┬── brain ── trader ── END
                └── sentiment ─┘
    Research and Sentiment run in parallel. Both must complete before Brain.
    """
    graph = StateGraph(AgentState)

    graph.add_node("research", research_node)
    graph.add_node("sentiment", sentiment_node)
    graph.add_node("brain", brain_node)
    graph.add_node("trader", trader_node)

    # Fan-out: START → Research + Sentiment in parallel
    graph.add_edge(START, "research")
    graph.add_edge(START, "sentiment")

    # Fan-in: both converge to Brain
    graph.add_edge("research", "brain")
    graph.add_edge("sentiment", "brain")

    # Sequential: Brain → Trader → END
    graph.add_edge("brain", "trader")
    graph.add_edge("trader", END)

    return graph


class TradingGraph:
    """High-level wrapper around the compiled LangGraph pipeline."""

    def __init__(self, config: AgentConfig | None = None) -> None:
        self.config = config or AgentConfig()
        self._graph = build_graph().compile()

    def run(
        self,
        token: str | None = None,
        portfolio_state: dict | None = None,
        reflection_memory: list[str] | None = None,
    ) -> AgentState:
        """Execute the full trading pipeline for a token.

        Args:
            token: Asset to analyze (defaults to config.target_token)
            portfolio_state: Current portfolio (defaults to initial capital)
            reflection_memory: Past decision history

        Returns:
            Final AgentState with all agent outputs.
        """
        token = token or self.config.target_token

        if portfolio_state is None:
            portfolio_state = {
                "cash": self.config.initial_capital,
                "holdings": {},
                "net_worth": self.config.initial_capital,
                "trade_history": [],
            }

        initial_state: AgentState = {
            "token": token.upper(),
            "asset_type": self.config.asset_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "research_report": "",
            "sentiment_report": "",
            "brain_decision": "",
            "trade_result": "",
            "portfolio_state": portfolio_state,
            "market_data": {},
            "reflection_memory": reflection_memory or [],
        }

        logger.info("Starting trading pipeline for %s", token.upper())
        result = self._graph.invoke(initial_state)
        logger.info("Pipeline complete for %s", token.upper())

        return result
