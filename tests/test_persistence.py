"""Integration tests for the persistence layer (SQLite)."""

from __future__ import annotations


import pytest

from cryptoagent.persistence.database import Database
from cryptoagent.persistence.reflection_store import ReflectionStore
from cryptoagent.persistence.trade_logger import TradeLogger
from cryptoagent.signals.logger import SignalLogger


class TestDatabase:
    """Database creation and schema tests."""

    def test_schema_created(self, in_memory_db: Database) -> None:
        tables = in_memory_db.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()
        names = {row["name"] for row in tables}
        assert "trades" in names
        assert "reflections" in names
        assert "signals" in names
        assert "price_snapshots" in names
        assert "signal_outcomes" in names

    def test_schema_idempotent(self, in_memory_db: Database) -> None:
        # Accessing .conn again should not error
        _ = in_memory_db.conn
        tables = in_memory_db.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        assert len(tables) >= 5


class TestTradeLogger:
    """TradeLogger CRUD tests."""

    def _make_trade_result(
        self,
        action: str = "BUY",
        token: str = "SOL",
        price: float = 150.0,
        net_worth: float = 10000.0,
    ) -> dict:
        return {
            "brain_decision": {
                "action": action,
                "asset": token,
                "confidence": 7,
                "regime": "bull",
            },
            "execution": {
                "trade": {
                    "token": token,
                    "action": action,
                    "price": price,
                    "quantity": 1.0,
                    "fee": 0.15,
                },
                "updated_portfolio": {
                    "cash": 5000.0,
                    "holdings": {token: 10.0},
                    "net_worth": net_worth,
                },
            },
        }

    def test_log_and_get_recent(self, in_memory_db: Database) -> None:
        logger = TradeLogger(in_memory_db)
        logger.log_trade(self._make_trade_result())
        trades = logger.get_recent(limit=5)
        assert len(trades) == 1
        assert trades[0]["action"] == "BUY"
        assert trades[0]["token"] == "SOL"

    def test_get_recent_ordering(self, in_memory_db: Database) -> None:
        logger = TradeLogger(in_memory_db)
        logger.log_trade(self._make_trade_result(action="BUY"))
        logger.log_trade(self._make_trade_result(action="SELL"))
        trades = logger.get_recent(limit=5)
        # Most recent first
        assert trades[0]["action"] == "SELL"
        assert trades[1]["action"] == "BUY"

    def test_get_daily_pnl_single_trade(self, in_memory_db: Database) -> None:
        logger = TradeLogger(in_memory_db)
        logger.log_trade(self._make_trade_result())
        pnl = logger.get_daily_pnl()
        # Only 1 trade today → returns 0
        assert pnl == 0.0

    def test_get_daily_pnl_two_trades(self, in_memory_db: Database) -> None:
        logger = TradeLogger(in_memory_db)
        logger.log_trade(self._make_trade_result(net_worth=10000.0))
        logger.log_trade(self._make_trade_result(net_worth=10500.0))
        pnl = logger.get_daily_pnl()
        assert pnl == pytest.approx(500.0)


class TestReflectionStore:
    """ReflectionStore CRUD tests."""

    def test_insert_and_get_level1(self, in_memory_db: Database) -> None:
        store = ReflectionStore(in_memory_db)
        store.insert(level=1, text="Good trade.", regime="bull")
        results = store.get_recent_level1(limit=5)
        assert len(results) == 1
        assert results[0] == "Good trade."

    def test_insert_and_get_cross_trial(self, in_memory_db: Database) -> None:
        store = ReflectionStore(in_memory_db)
        store.insert(level=2, text="Strategic review.", regime="bull")
        results = store.get_latest_cross_trial(limit=5)
        assert len(results) == 1
        assert results[0] == "Strategic review."

    def test_cross_trial_excludes_level1(self, in_memory_db: Database) -> None:
        store = ReflectionStore(in_memory_db)
        store.insert(level=1, text="Level 1 text.", regime="bull")
        results = store.get_latest_cross_trial(limit=5)
        assert len(results) == 0

    def test_count_since_last_level2(self, in_memory_db: Database) -> None:
        store = ReflectionStore(in_memory_db)
        # No level 2 yet → all level 1s count
        store.insert(level=1, text="r1", regime="bull")
        store.insert(level=1, text="r2", regime="bull")
        assert store.count_since_last_level2() == 2

        # Add level 2 → reset count
        store.insert(level=2, text="strategic", regime="bull")
        assert store.count_since_last_level2() == 0

        # Add more level 1s after level 2
        store.insert(level=1, text="r3", regime="bear")
        assert store.count_since_last_level2() == 1

    def test_get_recent_level1_limit(self, in_memory_db: Database) -> None:
        store = ReflectionStore(in_memory_db)
        for i in range(10):
            store.insert(level=1, text=f"Reflection {i}", regime="bull")
        results = store.get_recent_level1(limit=3)
        assert len(results) == 3

    def test_cross_trial_ordering(self, in_memory_db: Database) -> None:
        store = ReflectionStore(in_memory_db)
        store.insert(level=2, text="First review.", regime="bull")
        store.insert(level=2, text="Second review.", regime="bear")
        results = store.get_latest_cross_trial(limit=5)
        # Most recent first
        assert results[0] == "Second review."


class TestSignalLogger:
    """SignalLogger CRUD tests."""

    def test_log_signals_and_retrieve(self, in_memory_db: Database) -> None:
        logger = SignalLogger(in_memory_db)
        signals = [
            {
                "name": "rsi_14",
                "source": "technical",
                "direction": "bullish",
                "confidence": 0.8,
                "raw_value": 25.0,
            },
        ]
        logger.log_signals("SOL", signals, price=150.0, volume_24h=1e9)

        # Check signals table
        rows = in_memory_db.conn.execute("SELECT * FROM signals").fetchall()
        assert len(rows) == 1
        assert dict(rows[0])["name"] == "rsi_14"

        # Check price snapshot
        prices = in_memory_db.conn.execute("SELECT * FROM price_snapshots").fetchall()
        assert len(prices) == 1
        assert dict(prices[0])["price"] == 150.0

    def test_get_unevaluated_signals(self, in_memory_db: Database) -> None:
        logger = SignalLogger(in_memory_db)

        # Insert a signal backdated 5 hours
        from datetime import timedelta

        ts = (
            __import__("datetime").datetime.now(__import__("datetime").timezone.utc)
            - timedelta(hours=5)
        ).isoformat()
        conn = in_memory_db.conn
        conn.execute(
            "INSERT INTO signals (timestamp, token, name, source, direction, "
            "confidence, raw_value) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (ts, "SOL", "test", "technical", "bullish", 0.5, 1.0),
        )
        conn.commit()

        results = logger.get_unevaluated_signals("SOL", "4h", min_age_hours=4.0)
        assert len(results) == 1

    def test_get_signal_price(self, in_memory_db: Database) -> None:
        logger = SignalLogger(in_memory_db)
        signals = [
            {
                "name": "macd",
                "source": "technical",
                "direction": "bullish",
                "confidence": 0.6,
                "raw_value": 2.0,
            },
        ]
        logger.log_signals("SOL", signals, price=142.5)

        # Get the signal ID
        row = in_memory_db.conn.execute("SELECT id FROM signals LIMIT 1").fetchone()
        price = logger.get_signal_price(row["id"])
        assert price == 142.5

    def test_get_signal_price_missing(self, in_memory_db: Database) -> None:
        logger = SignalLogger(in_memory_db)
        assert logger.get_signal_price(9999) is None
