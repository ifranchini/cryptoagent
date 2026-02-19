"""Reflection Manager — Level 1 (per-cycle) and Level 2 (cross-trial) reflections."""

from __future__ import annotations

import json
import logging

from cryptoagent.llm.client import call_llm
from cryptoagent.persistence.database import Database
from cryptoagent.persistence.reflection_store import ReflectionStore

logger = logging.getLogger(__name__)

_LEVEL1_SYSTEM = """\
You are a trading reflection assistant. Summarize the decision, outcome, and lesson \
learned from this trading cycle in 2-3 sentences. Be specific about what worked or \
didn't work and why. Focus on actionable insights."""

_LEVEL2_SYSTEM = """\
You are a strategic trading advisor. Review the recent per-cycle reflections below and \
produce a cross-trial strategic review. Identify patterns across decisions, recurring \
mistakes, and recommend specific adjustments to the trading strategy. \
Keep it under 200 words. Be direct and actionable."""


class ReflectionManager:
    """Generates and stores Level 1 + Level 2 reflections."""

    def __init__(
        self,
        db: Database,
        model: str = "openai/gpt-4o-mini",
        cycle_length: int = 5,
    ) -> None:
        self._store = ReflectionStore(db)
        self._model = model
        self._cycle_length = cycle_length

    def generate_level1(
        self,
        brain_decision: dict,
        trade_result: dict,
        regime: str = "unknown",
    ) -> str:
        """Generate a per-cycle reflection and store it.

        Args:
            brain_decision: Parsed brain decision dict.
            trade_result: Parsed trade result dict.
            regime: Current market regime.

        Returns:
            The reflection text.
        """
        action = brain_decision.get("action", "HOLD")
        confidence = brain_decision.get("confidence", "?")
        rationale = brain_decision.get("rationale", "")
        executed = trade_result.get("executed", False)

        execution_info = ""
        if executed and "execution" in trade_result:
            trade = trade_result["execution"].get("trade", {})
            execution_info = (
                f"Trade executed: {trade.get('action')} {trade.get('quantity', 0):.4f} "
                f"@ ${trade.get('price', 0):,.2f}"
            )
        elif not executed:
            execution_info = f"Trade not executed: {trade_result.get('reason', 'unknown')}"

        user_prompt = (
            f"Decision: {action} (confidence {confidence}/10)\n"
            f"Rationale: {rationale}\n"
            f"Regime: {regime}\n"
            f"Outcome: {execution_info}\n\n"
            f"Summarize the lesson from this cycle."
        )

        try:
            reflection = call_llm(
                model=self._model,
                system=_LEVEL1_SYSTEM,
                user=user_prompt,
                temperature=0.3,
                max_tokens=256,
            )
        except Exception as e:
            logger.warning("Level 1 reflection LLM call failed: %s", e)
            reflection = f"[Auto] {action} decision with confidence {confidence}. {execution_info}"

        self._store.insert(level=1, text=reflection, regime=regime)
        logger.info("[Reflection] Level 1 stored")
        return reflection

    def maybe_generate_level2(self, regime: str = "unknown") -> str | None:
        """Generate a Level 2 cross-trial reflection if enough cycles have passed.

        Returns the reflection text if generated, else None.
        """
        cycles_since = self._store.count_since_last_level2()
        if cycles_since < self._cycle_length:
            logger.info(
                "[Reflection] %d/%d cycles since last Level 2 — skipping",
                cycles_since, self._cycle_length,
            )
            return None

        # Gather recent Level 1 reflections
        recent = self._store.get_recent_level1(limit=self._cycle_length * 2)
        if not recent:
            return None

        reflections_text = "\n".join(f"- {r}" for r in recent)

        user_prompt = (
            f"## Recent Per-Cycle Reflections ({len(recent)} cycles)\n"
            f"{reflections_text}\n\n"
            f"Current regime: {regime}\n\n"
            f"Produce your strategic cross-trial review."
        )

        try:
            review = call_llm(
                model=self._model,
                system=_LEVEL2_SYSTEM,
                user=user_prompt,
                temperature=0.4,
                max_tokens=512,
            )
        except Exception as e:
            logger.warning("Level 2 reflection LLM call failed: %s", e)
            return None

        self._store.insert(level=2, text=review, regime=regime)
        logger.info("[Reflection] Level 2 cross-trial review stored")
        return review

    def get_cross_trial_reflections(self, limit: int = 3) -> list[str]:
        """Load the latest cross-trial reflections for Brain prompt injection."""
        return self._store.get_latest_cross_trial(limit=limit)
