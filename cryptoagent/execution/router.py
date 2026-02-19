"""Execution router — directs trades to the appropriate venue."""

from __future__ import annotations

import logging

from cryptoagent.execution.paper_trade import execute_paper_trade

logger = logging.getLogger(__name__)


def execute_trade(
    action: str,
    token: str,
    size_pct: float,
    portfolio_state: dict,
    current_price: float,
    fee_pct: float = 0.001,
    mode: str = "paper",
) -> dict:
    """Route trade execution to the appropriate backend.

    Args:
        mode: "paper" for simulation, "live" for real execution (not yet implemented).
    """
    if mode == "paper":
        return execute_paper_trade(
            action=action,
            token=token,
            size_pct=size_pct,
            portfolio_state=portfolio_state,
            current_price=current_price,
            fee_pct=fee_pct,
        )

    if mode == "live":
        raise NotImplementedError(
            "Live trading is not implemented yet. Use --execution-mode paper."
        )

    raise ValueError(f"Unknown execution mode: {mode}")
