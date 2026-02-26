"""Persist signals and price snapshots to SQLite."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from cryptoagent.persistence.database import Database

logger = logging.getLogger(__name__)


class SignalLogger:
    """Logs signals and price snapshots, queries for evaluation."""

    def __init__(self, db: Database) -> None:
        self._db = db

    def log_signals(
        self,
        token: str,
        signals: list[dict],
        price: float,
        volume_24h: float | None = None,
    ) -> None:
        """Batch-insert signals and a price snapshot for this cycle.

        Args:
            token: Token symbol (e.g., "SOL").
            signals: List of signal dicts from extractor.
            price: Current price at time of signal extraction.
            volume_24h: Optional 24h volume.
        """
        now = datetime.now(timezone.utc).isoformat()
        conn = self._db.conn

        # Insert price snapshot
        conn.execute(
            "INSERT INTO price_snapshots (timestamp, token, price, volume_24h) VALUES (?, ?, ?, ?)",
            (now, token.upper(), price, volume_24h),
        )

        # Batch insert signals
        for sig in signals:
            conn.execute(
                """INSERT INTO signals (timestamp, token, name, source, direction, confidence, raw_value)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    now,
                    token.upper(),
                    sig["name"],
                    sig["source"],
                    sig["direction"],
                    sig["confidence"],
                    sig.get("raw_value"),
                ),
            )

        conn.commit()
        logger.info(
            "Logged %d signals + price snapshot for %s @ $%.2f",
            len(signals),
            token,
            price,
        )

    def get_unevaluated_signals(
        self,
        token: str,
        timeframe: str,
        min_age_hours: float,
    ) -> list[dict]:
        """Get signals old enough for a given timeframe but not yet evaluated.

        Args:
            token: Token symbol.
            timeframe: Timeframe label (e.g., "4h", "24h", "7d").
            min_age_hours: Minimum age in hours for the signal to be eligible.

        Returns:
            List of dicts with signal fields + id.
        """
        cutoff = _hours_ago_iso(min_age_hours)
        cursor = self._db.conn.execute(
            """SELECT s.id, s.timestamp, s.name, s.source, s.direction, s.confidence, s.raw_value
               FROM signals s
               WHERE s.token = ?
                 AND s.timestamp <= ?
                 AND s.id NOT IN (
                     SELECT signal_id FROM signal_outcomes WHERE timeframe = ?
                 )
               ORDER BY s.timestamp ASC""",
            (token.upper(), cutoff, timeframe),
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_price_at(self, token: str, timestamp: str) -> float | None:
        """Get the price snapshot closest to (but not before) the given timestamp."""
        cursor = self._db.conn.execute(
            """SELECT price FROM price_snapshots
               WHERE token = ? AND timestamp >= ?
               ORDER BY timestamp ASC LIMIT 1""",
            (token.upper(), timestamp),
        )
        row = cursor.fetchone()
        return float(row["price"]) if row else None

    def get_signal_price(self, signal_id: int) -> float | None:
        """Get the price at the time a signal was logged.

        Looks up the price_snapshots closest to the signal's timestamp.
        """
        cursor = self._db.conn.execute(
            "SELECT timestamp, token FROM signals WHERE id = ?",
            (signal_id,),
        )
        row = cursor.fetchone()
        if not row:
            return None

        price_cursor = self._db.conn.execute(
            """SELECT price FROM price_snapshots
               WHERE token = ? AND timestamp <= ?
               ORDER BY timestamp DESC LIMIT 1""",
            (row["token"], row["timestamp"]),
        )
        price_row = price_cursor.fetchone()
        return float(price_row["price"]) if price_row else None


def _hours_ago_iso(hours: float) -> str:
    """Return ISO timestamp for N hours ago."""
    from datetime import timedelta

    dt = datetime.now(timezone.utc) - timedelta(hours=hours)
    return dt.isoformat()
