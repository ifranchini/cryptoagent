"""Unit tests for the signal evaluator."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone


from cryptoagent.persistence.database import Database
from cryptoagent.signals.evaluator import _check_direction, evaluate_pending_signals


class TestCheckDirection:
    """Test _check_direction logic."""

    def test_bullish_positive_change(self) -> None:
        assert _check_direction("bullish", 5.0) is True

    def test_bullish_negative_change(self) -> None:
        assert _check_direction("bullish", -2.0) is False

    def test_bearish_negative_change(self) -> None:
        assert _check_direction("bearish", -3.5) is True

    def test_bearish_positive_change(self) -> None:
        assert _check_direction("bearish", 1.0) is False

    def test_neutral_small_change(self) -> None:
        assert _check_direction("neutral", 0.5) is True

    def test_neutral_large_change(self) -> None:
        assert _check_direction("neutral", 2.0) is False

    def test_bullish_zero_change(self) -> None:
        assert _check_direction("bullish", 0.0) is False

    def test_bearish_zero_change(self) -> None:
        assert _check_direction("bearish", 0.0) is False


class TestEvaluatePendingSignals:
    """Integration tests for evaluate_pending_signals."""

    def _insert_old_signal(
        self,
        db: Database,
        token: str = "SOL",
        hours_ago: float = 5.0,
        direction: str = "bullish",
        price: float = 100.0,
    ) -> None:
        """Insert a signal and price snapshot backdated by hours_ago."""
        ts = (datetime.now(timezone.utc) - timedelta(hours=hours_ago)).isoformat()
        conn = db.conn
        conn.execute(
            "INSERT INTO price_snapshots (timestamp, token, price, volume_24h) "
            "VALUES (?, ?, ?, ?)",
            (ts, token, price, None),
        )
        conn.execute(
            "INSERT INTO signals (timestamp, token, name, source, direction, "
            "confidence, raw_value) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (ts, token, "test_signal", "technical", direction, 0.7, 1.0),
        )
        conn.commit()

    def test_no_pending_signals(self, in_memory_db: Database) -> None:
        count = evaluate_pending_signals(in_memory_db, "SOL", 150.0)
        assert count == 0

    def test_evaluates_old_enough_signal(self, in_memory_db: Database) -> None:
        self._insert_old_signal(in_memory_db, hours_ago=5.0, price=100.0)
        # Signal is >4h old, should be evaluated at 4h timeframe
        count = evaluate_pending_signals(in_memory_db, "SOL", 110.0)
        assert count >= 1

        # Verify outcome was recorded
        rows = in_memory_db.conn.execute(
            "SELECT * FROM signal_outcomes"
        ).fetchall()
        assert len(rows) >= 1
        row = dict(rows[0])
        assert row["timeframe"] == "4h"
        assert row["direction_correct"] == 1  # bullish + price went up

    def test_skips_too_recent_signal(self, in_memory_db: Database) -> None:
        self._insert_old_signal(in_memory_db, hours_ago=1.0)
        count = evaluate_pending_signals(in_memory_db, "SOL", 110.0)
        assert count == 0

    def test_skips_signal_without_price(self, in_memory_db: Database) -> None:
        ts = (datetime.now(timezone.utc) - timedelta(hours=5.0)).isoformat()
        conn = in_memory_db.conn
        # Insert signal but NO price snapshot
        conn.execute(
            "INSERT INTO signals (timestamp, token, name, source, direction, "
            "confidence, raw_value) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (ts, "SOL", "orphan", "technical", "bullish", 0.5, 1.0),
        )
        conn.commit()
        count = evaluate_pending_signals(in_memory_db, "SOL", 110.0)
        assert count == 0
