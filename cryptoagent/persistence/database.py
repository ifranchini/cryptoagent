"""Database connection manager supporting SQLite and PostgreSQL."""

from __future__ import annotations

import logging
import sqlite3
from pathlib import Path

logger = logging.getLogger(__name__)

_SCHEMA_SQLITE = """
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

CREATE TABLE IF NOT EXISTS signals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    token TEXT NOT NULL,
    name TEXT NOT NULL,
    source TEXT NOT NULL,
    direction TEXT NOT NULL,
    confidence REAL NOT NULL,
    raw_value REAL
);

CREATE TABLE IF NOT EXISTS price_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    token TEXT NOT NULL,
    price REAL NOT NULL,
    volume_24h REAL
);

CREATE TABLE IF NOT EXISTS signal_outcomes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    signal_id INTEGER NOT NULL REFERENCES signals(id),
    timeframe TEXT NOT NULL,
    price_at_signal REAL NOT NULL,
    price_at_eval REAL NOT NULL,
    price_change_pct REAL NOT NULL,
    direction_correct INTEGER NOT NULL,
    evaluated_at TEXT NOT NULL
);
"""

_SCHEMA_PG = """
CREATE TABLE IF NOT EXISTS trades (
    id SERIAL PRIMARY KEY,
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
    id SERIAL PRIMARY KEY,
    timestamp TEXT NOT NULL,
    level INTEGER NOT NULL CHECK (level IN (1, 2)),
    text TEXT NOT NULL,
    regime TEXT,
    performance_summary TEXT
);

CREATE TABLE IF NOT EXISTS signals (
    id SERIAL PRIMARY KEY,
    timestamp TEXT NOT NULL,
    token TEXT NOT NULL,
    name TEXT NOT NULL,
    source TEXT NOT NULL,
    direction TEXT NOT NULL,
    confidence REAL NOT NULL,
    raw_value REAL
);

CREATE TABLE IF NOT EXISTS price_snapshots (
    id SERIAL PRIMARY KEY,
    timestamp TEXT NOT NULL,
    token TEXT NOT NULL,
    price REAL NOT NULL,
    volume_24h REAL
);

CREATE TABLE IF NOT EXISTS signal_outcomes (
    id SERIAL PRIMARY KEY,
    signal_id INTEGER NOT NULL REFERENCES signals(id),
    timeframe TEXT NOT NULL,
    price_at_signal REAL NOT NULL,
    price_at_eval REAL NOT NULL,
    price_change_pct REAL NOT NULL,
    direction_correct BOOLEAN NOT NULL,
    evaluated_at TEXT NOT NULL
);
"""


class _PgCursorAdapter:
    """Wraps a psycopg2 cursor to return dict-like rows matching SQLite Row."""

    def __init__(self, cursor):
        self._cursor = cursor

    def fetchone(self):
        row = self._cursor.fetchone()
        if row is None:
            return None
        cols = [desc[0] for desc in self._cursor.description]
        return _DictRow(dict(zip(cols, row)))

    def fetchall(self):
        rows = self._cursor.fetchall()
        if not rows:
            return []
        cols = [desc[0] for desc in self._cursor.description]
        return [_DictRow(dict(zip(cols, r))) for r in rows]


class _DictRow(dict):
    """Dict subclass supporting both key and index access for Row compat."""

    def __getitem__(self, key):
        if isinstance(key, int):
            return list(self.values())[key]
        return super().__getitem__(key)


class _PgConnAdapter:
    """Wraps a psycopg2 connection to translate ? placeholders to %s."""

    def __init__(self, pg_conn):
        self._conn = pg_conn

    def execute(self, sql: str, params=None):
        translated = sql.replace("?", "%s")
        cursor = self._conn.cursor()
        cursor.execute(translated, params)
        return _PgCursorAdapter(cursor)

    def executescript(self, sql: str):
        cursor = self._conn.cursor()
        cursor.execute(sql)

    def commit(self):
        self._conn.commit()

    def close(self):
        self._conn.close()


class Database:
    """Manages a database connection (SQLite or PostgreSQL)."""

    def __init__(self, db_path: str = "data/cryptoagent.db") -> None:
        self._db_path = db_path
        self._is_pg = db_path.startswith("postgresql://")
        self._conn = None

    @property
    def conn(self):
        if self._conn is None:
            if self._is_pg:
                self._conn = self._connect_pg()
            else:
                self._conn = self._connect_sqlite()
            self._init_schema()
            logger.info("Database opened: %s", "PostgreSQL" if self._is_pg else self._db_path)
        return self._conn

    def _connect_sqlite(self) -> sqlite3.Connection:
        path = Path(self._db_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _connect_pg(self):
        import psycopg2

        pg_conn = psycopg2.connect(self._db_path)
        pg_conn.autocommit = False
        return _PgConnAdapter(pg_conn)

    def _init_schema(self) -> None:
        schema = _SCHEMA_PG if self._is_pg else _SCHEMA_SQLITE
        self.conn.executescript(schema)
        self.conn.commit()

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None
