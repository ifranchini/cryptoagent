"""Evaluate signal outcomes against actual price movements."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from cryptoagent.persistence.database import Database
from cryptoagent.signals.logger import SignalLogger

logger = logging.getLogger(__name__)

# Timeframes: label -> minimum age in hours before evaluation
TIMEFRAMES: dict[str, float] = {
    "4h": 4.0,
    "24h": 24.0,
    "7d": 168.0,
}


def evaluate_pending_signals(
    db: Database,
    token: str,
    current_price: float,
) -> int:
    """Evaluate all pending signals against current price.

    For each timeframe, finds signals old enough to evaluate and checks
    whether the signal's direction matched the actual price movement.

    Args:
        db: Database instance.
        token: Token symbol.
        current_price: Current price for evaluation.

    Returns:
        Total number of outcomes recorded.
    """
    signal_logger = SignalLogger(db)
    total_evaluated = 0

    for timeframe, min_hours in TIMEFRAMES.items():
        unevaluated = signal_logger.get_unevaluated_signals(
            token=token,
            timeframe=timeframe,
            min_age_hours=min_hours,
        )

        for sig in unevaluated:
            price_at_signal = signal_logger.get_signal_price(sig["id"])
            if price_at_signal is None or price_at_signal <= 0:
                continue

            price_change_pct = (
                (current_price - price_at_signal) / price_at_signal
            ) * 100
            direction_correct = _check_direction(sig["direction"], price_change_pct)

            db.conn.execute(
                """INSERT INTO signal_outcomes
                   (signal_id, timeframe, price_at_signal, price_at_eval,
                    price_change_pct, direction_correct, evaluated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    sig["id"],
                    timeframe,
                    price_at_signal,
                    current_price,
                    round(price_change_pct, 4),
                    1 if direction_correct else 0,
                    datetime.now(timezone.utc).isoformat(),
                ),
            )
            total_evaluated += 1

    if total_evaluated > 0:
        db.conn.commit()
        logger.info("Evaluated %d signal outcomes for %s", total_evaluated, token)

    return total_evaluated


def _check_direction(signal_direction: str, price_change_pct: float) -> bool:
    """Check if signal direction matched the actual price movement.

    A neutral signal is "correct" if price moved less than 1%.
    """
    if signal_direction == "bullish":
        return price_change_pct > 0
    if signal_direction == "bearish":
        return price_change_pct < 0
    # Neutral: correct if price didn't move much
    return abs(price_change_pct) < 1.0
