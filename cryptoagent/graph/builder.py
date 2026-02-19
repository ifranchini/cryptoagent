"""LangGraph pipeline — wires the 4 agents into a parallel-then-sequential flow."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

from langgraph.graph import END, START, StateGraph

from cryptoagent.agents.brain import brain_node
from cryptoagent.agents.research import research_node
from cryptoagent.agents.sentiment import sentiment_node
from cryptoagent.agents.trader import trader_node
from cryptoagent.config import AgentConfig
from cryptoagent.dataflows.aggregator import DataAggregator
from cryptoagent.graph.state import AgentState
from cryptoagent.persistence.database import Database
from cryptoagent.persistence.trade_logger import TradeLogger
from cryptoagent.reflection.manager import ReflectionManager
from cryptoagent.risk.sentinel import RiskSentinel

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

        # Phase 2: persistence + risk + reflection
        self._db = Database(self.config.db_path)
        self._trade_logger = TradeLogger(self._db)
        self._reflection_mgr = ReflectionManager(
            db=self._db,
            model=self.config.reflection_model,
            cycle_length=self.config.reflection_cycle_length,
        )
        self._risk_sentinel = RiskSentinel(
            max_daily_loss_pct=self.config.max_daily_loss_pct,
            max_drawdown_pct=self.config.max_drawdown_pct,
            volatility_spike_multiplier=self.config.volatility_spike_multiplier,
            initial_capital=self.config.initial_capital,
        )
        self._aggregator = DataAggregator(
            exchange=self.config.exchange, config=self.config,
        )

    def run(
        self,
        token: str | None = None,
        portfolio_state: dict | None = None,
        reflection_memory: list[str] | None = None,
    ) -> AgentState:
        """Execute the full trading pipeline for a token.

        Pre-pipeline: load reflections, risk pre-check, compute regime.
        Pipeline: 4-agent graph (unchanged topology).
        Post-pipeline: risk post-check, log trade, generate reflections.
        """
        token = token or self.config.target_token

        if portfolio_state is None:
            portfolio_state = {
                "cash": self.config.initial_capital,
                "holdings": {},
                "net_worth": self.config.initial_capital,
                "trade_history": [],
            }

        # --- PRE-PIPELINE ---

        # 1. Load cross-trial reflections from SQLite
        cross_trial = self._reflection_mgr.get_cross_trial_reflections(limit=3)

        # 2. Risk pre-check
        daily_pnl = self._trade_logger.get_daily_pnl()
        pre_risk = self._risk_sentinel.pre_check(portfolio_state, daily_pnl)
        risk_verdict = pre_risk["verdict"]

        # 3. Compute market regime from latest market data (quick fetch for regime only)
        market_regime = "unknown"
        regime_confidence = 0
        try:
            market_snapshot = self._aggregator.get_market_data(token.upper())
            regime_result = self._aggregator.get_market_regime(market_snapshot)
            market_regime = regime_result.get("regime", "unknown")
            regime_confidence = regime_result.get("confidence", 0)
        except Exception as e:
            logger.warning("Regime classification failed: %s", e)

        # Build initial state
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
            "onchain_data": {},
            "market_regime": market_regime,
            "regime_confidence": regime_confidence,
            "fear_greed_index": 50,
            "risk_verdict": risk_verdict,
            "cross_trial_reflections": cross_trial,
        }

        # If risk sentinel halts, force HOLD without running the pipeline
        if risk_verdict == "halt":
            logger.warning("Risk Sentinel halted pipeline: %s", pre_risk["reasons"])
            hold_decision = json.dumps({
                "action": "HOLD",
                "asset": token.upper(),
                "size_pct": 0,
                "confidence": 1,
                "regime": market_regime,
                "rationale": f"Risk Sentinel halt: {'; '.join(pre_risk['reasons'])}",
            })
            initial_state["brain_decision"] = hold_decision
            initial_state["trade_result"] = json.dumps({
                "executed": False,
                "reason": f"Risk Sentinel halt: {'; '.join(pre_risk['reasons'])}",
                "brain_decision": json.loads(hold_decision),
            })
            return initial_state

        # --- RUN PIPELINE ---
        logger.info("Starting trading pipeline for %s", token.upper())
        result = self._graph.invoke(initial_state)
        logger.info("Pipeline complete for %s", token.upper())

        # --- POST-PIPELINE ---

        # 5. Parse brain decision for post-checks
        try:
            brain_decision = json.loads(result.get("brain_decision", "{}"))
        except json.JSONDecodeError:
            brain_decision = {"action": "HOLD"}

        try:
            trade_result = json.loads(result.get("trade_result", "{}"))
        except json.JSONDecodeError:
            trade_result = {"executed": False}

        # 6. Log trade to SQLite
        if trade_result.get("executed"):
            self._trade_logger.log_trade(trade_result)

        # 7. Generate Level 1 reflection
        regime = brain_decision.get("regime", market_regime)
        l1_reflection = self._reflection_mgr.generate_level1(
            brain_decision=brain_decision,
            trade_result=trade_result,
            regime=regime,
        )

        # Append to in-memory reflection list for carry-forward
        memory = list(result.get("reflection_memory", []))
        memory.append(l1_reflection)
        result["reflection_memory"] = memory

        # 8. Maybe generate Level 2 reflection
        l2_reflection = self._reflection_mgr.maybe_generate_level2(regime=regime)

        # Store pipeline metadata
        result["market_regime"] = market_regime
        result["regime_confidence"] = regime_confidence
        result["risk_verdict"] = risk_verdict

        return result

    def close(self) -> None:
        """Close the database connection."""
        self._db.close()
