"""Integration tests for the reflection manager (uses mock LLM + in-memory DB)."""

from __future__ import annotations

from unittest.mock import patch


from cryptoagent.persistence.database import Database
from cryptoagent.reflection.manager import ReflectionManager


class TestLevel1:
    """Level 1 (per-cycle) reflection tests."""

    def test_generates_and_stores(self, in_memory_db: Database, mock_llm) -> None:
        mgr = ReflectionManager(in_memory_db, model="test-model", cycle_length=5)
        result = mgr.generate_level1(
            brain_decision={"action": "BUY", "confidence": 7, "rationale": "Strong signal."},
            trade_result={"executed": True, "execution": {"trade": {"action": "BUY", "quantity": 1.0, "price": 150.0}}},
            regime="bull",
        )
        assert result == "Mocked LLM reflection output."

        # Verify stored in DB
        rows = in_memory_db.conn.execute(
            "SELECT * FROM reflections WHERE level = 1"
        ).fetchall()
        assert len(rows) == 1

    def test_llm_failure_fallback(self, in_memory_db: Database) -> None:
        with patch("cryptoagent.reflection.manager.call_llm", side_effect=RuntimeError("API down")):
            mgr = ReflectionManager(in_memory_db, model="test-model")
            result = mgr.generate_level1(
                brain_decision={"action": "HOLD", "confidence": 3},
                trade_result={"executed": False, "reason": "risk halt"},
                regime="bear",
            )
        assert "[Auto]" in result
        assert "HOLD" in result

        # Still stored even on failure
        rows = in_memory_db.conn.execute(
            "SELECT * FROM reflections WHERE level = 1"
        ).fetchall()
        assert len(rows) == 1

    def test_not_executed_trade(self, in_memory_db: Database, mock_llm) -> None:
        mgr = ReflectionManager(in_memory_db, model="test-model")
        result = mgr.generate_level1(
            brain_decision={"action": "BUY", "confidence": 5, "rationale": "Test"},
            trade_result={"executed": False, "reason": "risk sentinel halt"},
            regime="sideways",
        )
        assert isinstance(result, str)


class TestLevel2:
    """Level 2 (cross-trial) reflection tests."""

    def test_skips_when_too_few_cycles(self, in_memory_db: Database) -> None:
        mgr = ReflectionManager(in_memory_db, model="test-model", cycle_length=5)
        # Only 2 level 1 reflections
        store = mgr._store
        store.insert(level=1, text="r1", regime="bull")
        store.insert(level=1, text="r2", regime="bull")

        result = mgr.maybe_generate_level2(regime="bull")
        assert result is None

    def test_generates_when_enough_cycles(self, in_memory_db: Database, mock_llm) -> None:
        mgr = ReflectionManager(in_memory_db, model="test-model", cycle_length=3)
        store = mgr._store
        for i in range(4):
            store.insert(level=1, text=f"Reflection {i}", regime="bull")

        result = mgr.maybe_generate_level2(regime="bull")
        assert result == "Mocked LLM reflection output."

        # Verify stored as level 2
        rows = in_memory_db.conn.execute(
            "SELECT * FROM reflections WHERE level = 2"
        ).fetchall()
        assert len(rows) == 1

    def test_no_level1_returns_none(self, in_memory_db: Database, mock_llm) -> None:
        mgr = ReflectionManager(in_memory_db, model="test-model", cycle_length=0)
        result = mgr.maybe_generate_level2(regime="bull")
        assert result is None

    def test_level2_llm_failure_returns_none(self, in_memory_db: Database) -> None:
        with patch("cryptoagent.reflection.manager.call_llm", side_effect=RuntimeError("fail")):
            mgr = ReflectionManager(in_memory_db, model="test-model", cycle_length=2)
            store = mgr._store
            for i in range(3):
                store.insert(level=1, text=f"r{i}", regime="bull")

            result = mgr.maybe_generate_level2(regime="bull")
        assert result is None


class TestCrossTrialRetrieval:
    """Test get_cross_trial_reflections."""

    def test_returns_limited_results(self, in_memory_db: Database) -> None:
        mgr = ReflectionManager(in_memory_db, model="test-model")
        store = mgr._store
        for i in range(5):
            store.insert(level=2, text=f"Review {i}", regime="bull")

        results = mgr.get_cross_trial_reflections(limit=3)
        assert len(results) == 3

    def test_empty_db_returns_empty(self, in_memory_db: Database) -> None:
        mgr = ReflectionManager(in_memory_db, model="test-model")
        results = mgr.get_cross_trial_reflections()
        assert results == []
