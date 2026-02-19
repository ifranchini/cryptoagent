"""SQLite connection manager and schema initialization."""

from __future__ import annotations

import logging
import sqlite3
from pathlib import Path

logger = logging.getLogger(__name__)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    token TEXT NOT NULL,
    action TEXT NOT NULL,
    price REAL,
    quantity REAL,
    fee REAL,
    portfolio_snapshot TEXT,
    brain_decision TEXT,
    regime TEXT,
    confidence INTEGER
);

CREATE TABLE IF NOT EXISTS reflections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    level INTEGER NOT NULL CHECK (level IN (1, 2)),
    text TEXT NOT NULL,
    regime TEXT,
    performance_summary TEXT
);
"""


class Database:
    """Manages a single SQLite database connection."""

    def __init__(self, db_path: str = "data/cryptoagent.db") -> None:
        self._path = Path(db_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._conn: sqlite3.Connection | None = None

    @property
    def conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(str(self._path))
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._init_schema()
            logger.info("Database opened at %s", self._path)
        return self._conn

    def _init_schema(self) -> None:
        self.conn.executescript(_SCHEMA)
        self.conn.commit()

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None
