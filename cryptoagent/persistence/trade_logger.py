"""Trade history CRUD operations."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

from cryptoagent.persistence.database import Database

logger = logging.getLogger(__name__)


class TradeLogger:
    """Logs and queries trade history in SQLite."""

    def __init__(self, db: Database) -> None:
        self._db = db

    def log_trade(self, result: dict) -> None:
        """Persist a trade result from the pipeline.

        Accepts the full trade_result dict produced by the Trader agent.
        """
        brain = result.get("brain_decision", {})
        execution = result.get("execution", {})
        trade = execution.get("trade", {})
        portfolio = execution.get("updated_portfolio", {})

        self._db.conn.execute(
            """INSERT INTO trades
               (timestamp, token, action, price, quantity, fee,
                portfolio_snapshot, brain_decision, regime, confidence)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                datetime.now(timezone.utc).isoformat(),
                brain.get("asset", trade.get("token", "")),
                brain.get("action", "HOLD"),
                trade.get("price", 0),
                trade.get("quantity", 0),
                trade.get("fee", 0),
                json.dumps(portfolio, default=str),
                json.dumps(brain, default=str),
                brain.get("regime", "unknown"),
                brain.get("confidence", 0),
            ),
        )
        self._db.conn.commit()
        logger.info("Trade logged: %s %s", brain.get("action"), brain.get("asset"))

    def get_recent(self, limit: int = 10) -> list[dict]:
        """Return the most recent trades."""
        cursor = self._db.conn.execute(
            "SELECT * FROM trades ORDER BY id DESC LIMIT ?", (limit,)
        )
        rows = cursor.fetchall()
        return [dict(r) for r in rows]

    def get_daily_pnl(self) -> float:
        """Compute rough daily PnL from today's trades.

        Compares net_worth in the latest portfolio snapshot to the earliest today.
        Returns 0.0 if fewer than 2 trades exist today.
        """
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        cursor = self._db.conn.execute(
            "SELECT portfolio_snapshot FROM trades WHERE timestamp LIKE ? ORDER BY id",
            (f"{today}%",),
        )
        rows = cursor.fetchall()
        if len(rows) < 2:
            return 0.0

        first = json.loads(rows[0]["portfolio_snapshot"])
        last = json.loads(rows[-1]["portfolio_snapshot"])
        return last.get("net_worth", 0) - first.get("net_worth", 0)
