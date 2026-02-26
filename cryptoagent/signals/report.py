"""Generate signal accuracy report for Brain agent context injection."""

from __future__ import annotations

import logging

from cryptoagent.persistence.database import Database

logger = logging.getLogger(__name__)

_MIN_SAMPLES = 5
_LOOKBACK_DAYS = 90
_TIMEFRAMES = ("4h", "24h", "7d")


def generate_signal_report(db: Database, token: str) -> str:
    """Generate a human-readable signal accuracy report.

    Queries signal_outcomes grouped by signal name + timeframe, computes
    hit rates. Only includes signals with >= MIN_SAMPLES evaluated outcomes.

    Returns empty string if insufficient data, so the Brain prompt is
    unaffected until enough history accumulates.
    """
    # Check if we have enough total outcomes
    total_cursor = db.conn.execute(
        """SELECT COUNT(*) as cnt FROM signal_outcomes so
           JOIN signals s ON so.signal_id = s.id
           WHERE s.token = ?""",
        (token.upper(),),
    )
    total_row = total_cursor.fetchone()
    if not total_row or total_row["cnt"] < _MIN_SAMPLES:
        return ""

    # Get accuracy per signal per timeframe
    cursor = db.conn.execute(
        """SELECT
               s.name,
               so.timeframe,
               COUNT(*) as samples,
               SUM(so.direction_correct) as correct,
               AVG(so.price_change_pct) as avg_change
           FROM signal_outcomes so
           JOIN signals s ON so.signal_id = s.id
           WHERE s.token = ?
             AND so.evaluated_at >= datetime('now', ?)
           GROUP BY s.name, so.timeframe
           HAVING COUNT(*) >= ?
           ORDER BY s.name, so.timeframe""",
        (token.upper(), f"-{_LOOKBACK_DAYS} days", _MIN_SAMPLES),
    )

    rows = cursor.fetchall()
    if not rows:
        return ""

    # Organize into {signal_name: {timeframe: {acc, samples}}}
    accuracy_data: dict[str, dict[str, dict]] = {}
    for row in rows:
        name = row["name"]
        tf = row["timeframe"]
        samples = row["samples"]
        correct = row["correct"]
        acc_pct = round((correct / samples) * 100) if samples > 0 else 0

        if name not in accuracy_data:
            accuracy_data[name] = {}
        accuracy_data[name][tf] = {"acc": acc_pct, "samples": samples}

    # Format report
    lines = [
        f"SIGNAL ACCURACY REPORT for {token.upper()} (last {_LOOKBACK_DAYS} days):"
    ]
    lines.append(
        f"{'Signal':<20}| {'4h acc.':<10}| {'24h acc.':<10}| {'7d acc.':<10}| Samples"
    )
    lines.append("-" * 72)

    for name in sorted(accuracy_data.keys()):
        tf_data = accuracy_data[name]
        cells = []
        max_samples = 0
        for tf in _TIMEFRAMES:
            if tf in tf_data:
                cells.append(f"{tf_data[tf]['acc']}%")
                max_samples = max(max_samples, tf_data[tf]["samples"])
            else:
                cells.append("N/A")

        lines.append(
            f"{name:<20}| {cells[0]:<10}| {cells[1]:<10}| {cells[2]:<10}| {max_samples}"
        )

    lines.append("")
    lines.append(
        f"Note: Accuracy based on evaluated cycles. Minimum {_MIN_SAMPLES} samples required."
    )

    report = "\n".join(lines)
    logger.info(
        "Generated signal accuracy report for %s (%d signals)",
        token,
        len(accuracy_data),
    )
    return report
