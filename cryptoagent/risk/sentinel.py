"""Risk Sentinel — pre/post pipeline threshold checks. No LLM calls."""

from __future__ import annotations

import json
import logging

logger = logging.getLogger(__name__)


class RiskSentinel:
    """Pure threshold-based risk checks that can halt or modify trades."""

    def __init__(
        self,
        max_daily_loss_pct: float = 5.0,
        max_drawdown_pct: float = 15.0,
        volatility_spike_multiplier: float = 2.0,
        initial_capital: float = 10000.0,
    ) -> None:
        self.max_daily_loss_pct = max_daily_loss_pct
        self.max_drawdown_pct = max_drawdown_pct
        self.volatility_spike_multiplier = volatility_spike_multiplier
        self.initial_capital = initial_capital

    def pre_check(
        self,
        portfolio: dict,
        daily_pnl: float = 0.0,
    ) -> dict:
        """Pre-pipeline risk check. Can force HOLD.

        Args:
            portfolio: Current portfolio state dict.
            daily_pnl: Today's realized PnL (from TradeLogger).

        Returns:
            {"verdict": "proceed"|"halt", "reasons": [...]}
        """
        reasons = []
        net_worth = portfolio.get("net_worth", self.initial_capital)

        # Daily loss check
        if net_worth > 0 and daily_pnl < 0:
            daily_loss_pct = abs(daily_pnl) / net_worth * 100
            if daily_loss_pct >= self.max_daily_loss_pct:
                reasons.append(
                    f"Daily loss {daily_loss_pct:.1f}% exceeds limit {self.max_daily_loss_pct}%"
                )

        # Drawdown check
        drawdown_pct = (1 - net_worth / self.initial_capital) * 100 if self.initial_capital > 0 else 0
        if drawdown_pct >= self.max_drawdown_pct:
            reasons.append(
                f"Drawdown {drawdown_pct:.1f}% exceeds limit {self.max_drawdown_pct}%"
            )

        verdict = "halt" if reasons else "proceed"
        if verdict == "halt":
            logger.warning("[Risk Sentinel] PRE-CHECK HALT: %s", "; ".join(reasons))
        else:
            logger.info("[Risk Sentinel] Pre-check passed")

        return {"verdict": verdict, "reasons": reasons}

    def post_check(
        self,
        brain_decision: dict,
        portfolio: dict,
        market_data: dict,
    ) -> dict:
        """Post-pipeline risk check. Can modify or veto a trade.

        Args:
            brain_decision: Parsed brain decision dict.
            portfolio: Current portfolio state.
            market_data: Market snapshot with indicators.

        Returns:
            {"verdict": "proceed"|"reduce"|"halt", "modified_size_pct": float, "reasons": [...]}
        """
        reasons = []
        action = brain_decision.get("action", "HOLD")
        size_pct = float(brain_decision.get("size_pct", 0))

        if action == "HOLD" or size_pct == 0:
            return {"verdict": "proceed", "modified_size_pct": 0, "reasons": []}

        modified_size = size_pct
        indicators = market_data.get("indicators", {})

        # ATR volatility spike check
        atr = indicators.get("atr_14", 0)
        price = market_data.get("current_price", 0)
        if atr > 0 and price > 0:
            atr_pct = atr / price * 100
            # If ATR is spiking (> multiplier * normal range ~2-3%), halve position
            if atr_pct > self.volatility_spike_multiplier * 2.5:
                modified_size = size_pct / 2
                reasons.append(
                    f"ATR spike detected ({atr_pct:.1f}% of price). Position halved."
                )

        # Excessive position concentration check
        net_worth = portfolio.get("net_worth", self.initial_capital)
        cash = portfolio.get("cash", 0)
        if action == "BUY" and net_worth > 0:
            trade_value = cash * (modified_size / 100)
            position_pct = trade_value / net_worth * 100
            if position_pct > 30:
                modified_size = min(modified_size, 25)
                reasons.append(
                    f"Position would be {position_pct:.0f}% of portfolio. Capped at 25%."
                )

        if modified_size != size_pct:
            verdict = "reduce"
        else:
            verdict = "proceed"

        if reasons:
            logger.warning("[Risk Sentinel] POST-CHECK: %s", "; ".join(reasons))
        else:
            logger.info("[Risk Sentinel] Post-check passed")

        return {
            "verdict": verdict,
            "modified_size_pct": round(modified_size, 2),
            "reasons": reasons,
        }
