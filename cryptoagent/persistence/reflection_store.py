"""Reflection memory CRUD operations."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

from cryptoagent.persistence.database import Database

logger = logging.getLogger(__name__)


class ReflectionStore:
    """Stores and retrieves reflection entries in SQLite."""

    def __init__(self, db: Database) -> None:
        self._db = db

    def insert(
        self,
        level: int,
        text: str,
        regime: str = "unknown",
        performance_summary: str = "",
    ) -> None:
        """Insert a reflection entry (level 1 = per-cycle, level 2 = cross-trial)."""
        self._db.conn.execute(
            """INSERT INTO reflections (timestamp, level, text, regime, performance_summary)
               VALUES (?, ?, ?, ?, ?)""",
            (
                datetime.now(timezone.utc).isoformat(),
                level,
                text,
                regime,
                performance_summary,
            ),
        )
        self._db.conn.commit()
        logger.info("Reflection stored: level=%d, regime=%s", level, regime)

    def get_latest_cross_trial(self, limit: int = 3) -> list[str]:
        """Return the most recent Level 2 (cross-trial) reflection texts."""
        cursor = self._db.conn.execute(
            "SELECT text FROM reflections WHERE level = 2 ORDER BY id DESC LIMIT ?",
            (limit,),
        )
        return [row["text"] for row in cursor.fetchall()]

    def get_recent_level1(self, limit: int = 10) -> list[str]:
        """Return the most recent Level 1 (per-cycle) reflection texts."""
        cursor = self._db.conn.execute(
            "SELECT text FROM reflections WHERE level = 1 ORDER BY id DESC LIMIT ?",
            (limit,),
        )
        return [row["text"] for row in cursor.fetchall()]

    def count_since_last_level2(self) -> int:
        """Count Level 1 reflections since the last Level 2 reflection."""
        cursor = self._db.conn.execute(
            "SELECT MAX(id) as last_id FROM reflections WHERE level = 2"
        )
        row = cursor.fetchone()
        last_l2_id = row["last_id"] if row and row["last_id"] else 0

        cursor = self._db.conn.execute(
            "SELECT COUNT(*) as cnt FROM reflections WHERE level = 1 AND id > ?",
            (last_l2_id,),
        )
        return cursor.fetchone()["cnt"]
