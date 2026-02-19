"""Sentiment Agent — analyzes social signals and news for market sentiment."""

from __future__ import annotations

import logging

from cryptoagent.config import AgentConfig
from cryptoagent.dataflows.aggregator import DataAggregator
from cryptoagent.graph.state import AgentState
from cryptoagent.llm.client import call_llm

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
You are a crypto/financial sentiment analyst. Your job is to analyze social media signals, \
news, and crowd sentiment to produce a sentiment report.

Rules:
1. Separate [FACTUAL] observations (e.g., "Fear & Greed Index is 55") from \
[SUBJECTIVE] interpretations (e.g., "Market mood feels cautious").
2. Assess overall sentiment direction: Strong Bearish / Bearish / Neutral / Bullish / Strong Bullish.
3. Rate sentiment intensity from 1 (very weak signal) to 10 (very strong signal).
4. Note any divergences between different sentiment sources (Reddit vs Twitter vs Fear & Greed).
5. When real Reddit data is available, analyze the specific post titles and engagement levels.
6. When Twitter data is available, reference the sentiment ratio (bullish/bearish/neutral split).
7. Always anchor on the Fear & Greed Index as a baseline, then layer social signals on top.
8. Keep it under 400 words.
"""


def _build_user_prompt(token: str, sentiment_data: dict) -> str:
    sections = [f"Analyze the following sentiment data for {token} and produce your sentiment report.\n"]

    # Fear & Greed
    fng_val = sentiment_data.get("fear_greed_index", "N/A")
    fng_label = sentiment_data.get("fear_greed_label", "N/A")
    sections.append(f"## Fear & Greed Index\nValue: {fng_val} ({fng_label})\n")

    # Reddit
    reddit = sentiment_data.get("reddit", {})
    if reddit and reddit.get("source") != "error":
        posts = reddit.get("posts", [])
        tone = reddit.get("overall_tone", "no_data")
        volume = reddit.get("volume", 0)
        sections.append(f"## Reddit Sentiment\nOverall tone: {tone} | Post volume: {volume}")
        if posts:
            sections.append("Top posts by engagement:")
            for p in posts[:5]:
                sections.append(
                    f"- [{p.get('score', 0)} pts, {p.get('num_comments', 0)} comments] "
                    f"{p.get('title', '')}"
                )
        sections.append("")
    else:
        sections.append("## Reddit Sentiment\nData unavailable.\n")

    # Twitter
    twitter = sentiment_data.get("twitter", {})
    if twitter and twitter.get("volume", 0) > 0:
        ratio = twitter.get("sentiment_ratio", {})
        sections.append(
            f"## Twitter/X Sentiment\n"
            f"Volume: {twitter.get('volume', 0)} tweets\n"
            f"Sentiment split: Bullish {ratio.get('bullish', 0):.0%} / "
            f"Bearish {ratio.get('bearish', 0):.0%} / "
            f"Neutral {ratio.get('neutral', 0):.0%}"
        )
        tweets = twitter.get("tweets", [])
        if tweets:
            sections.append("Top tweets:")
            for t in tweets[:3]:
                sections.append(f"- [{t.get('likes', 0)} likes] {t.get('text', '')[:120]}")
        sections.append("")
    else:
        note = twitter.get("note", "Twitter data not configured") if twitter else "No Twitter data"
        sections.append(f"## Twitter/X Sentiment\n{note}\n")

    sections.append("Produce a concise sentiment report with direction, intensity, and key observations.")
    return "\n".join(sections)


def sentiment_node(state: AgentState) -> dict:
    """LangGraph node: Sentiment Agent.

    Fetches real social/news sentiment data, sends to LLM for analysis.
    """
    agent_config = AgentConfig()
    token = state["token"]
    aggregator = DataAggregator(exchange=agent_config.exchange, config=agent_config)

    logger.info("[Sentiment Agent] Collecting sentiment data for %s", token)

    sentiment_data = aggregator.get_sentiment_data(token)

    user_prompt = _build_user_prompt(token, sentiment_data)

    logger.info("[Sentiment Agent] Calling LLM: %s", agent_config.sentiment_model)
    report = call_llm(
        model=agent_config.sentiment_model,
        system=SYSTEM_PROMPT,
        user=user_prompt,
    )

    logger.info("[Sentiment Agent] Report generated (%d chars)", len(report))

    fng = sentiment_data.get("fear_greed_index", 50)

    return {
        "sentiment_report": report,
        "fear_greed_index": fng,
    }
