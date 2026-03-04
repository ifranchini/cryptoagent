"""Unit tests for signal extraction from AgentState."""

from __future__ import annotations

import json

import pytest

from cryptoagent.signals.extractor import (
    _direction_from_action,
    _direction_from_fear_greed,
    _direction_from_macd,
    _direction_from_regime,
    _direction_from_rsi,
    _direction_from_sma,
    _extract_brain,
    _extract_macro,
    _extract_onchain,
    _extract_sentiment,
    _extract_technical,
    extract_signals,
)


class TestDirectionHelpers:
    """Low-level direction classifiers."""

    @pytest.mark.parametrize(
        ("rsi", "expected"),
        [(20, "bullish"), (29.9, "bullish"), (50, "neutral"), (71, "bearish")],
    )
    def test_direction_from_rsi(self, rsi: float, expected: str) -> None:
        assert _direction_from_rsi(rsi) == expected

    @pytest.mark.parametrize(
        ("hist", "expected"),
        [(2.5, "bullish"), (-0.3, "bearish"), (0, "neutral")],
    )
    def test_direction_from_macd(self, hist: float, expected: str) -> None:
        assert _direction_from_macd(hist) == expected

    @pytest.mark.parametrize(
        ("pos", "expected"),
        [("above", "bullish"), ("below", "bearish"), ("", "neutral")],
    )
    def test_direction_from_sma(self, pos: str, expected: str) -> None:
        assert _direction_from_sma(pos) == expected

    @pytest.mark.parametrize(
        ("val", "expected"),
        [(10, "bullish"), (24, "bullish"), (50, "neutral"), (80, "bearish")],
    )
    def test_direction_from_fear_greed(self, val: int, expected: str) -> None:
        assert _direction_from_fear_greed(val) == expected

    @pytest.mark.parametrize(
        ("regime", "expected"),
        [
            ("bull", "bullish"),
            ("risk_on", "bullish"),
            ("bear", "bearish"),
            ("risk_off", "bearish"),
            ("sideways", "neutral"),
        ],
    )
    def test_direction_from_regime(self, regime: str, expected: str) -> None:
        assert _direction_from_regime(regime) == expected

    @pytest.mark.parametrize(
        ("action", "expected"),
        [("BUY", "bullish"), ("SELL", "bearish"), ("HOLD", "neutral")],
    )
    def test_direction_from_action(self, action: str, expected: str) -> None:
        assert _direction_from_action(action) == expected


class TestExtractTechnical:
    """Test _extract_technical with various indicator combinations."""

    def test_empty_indicators(self) -> None:
        assert _extract_technical({}) == []
        assert _extract_technical({"indicators": {}}) == []

    def test_rsi_oversold(self) -> None:
        data = {"indicators": {"rsi_14": 20.0}}
        signals = _extract_technical(data)
        rsi_sig = next(s for s in signals if s["name"] == "rsi_14")
        assert rsi_sig["direction"] == "bullish"

    def test_rsi_overbought(self) -> None:
        data = {"indicators": {"rsi_14": 80.0}}
        signals = _extract_technical(data)
        rsi_sig = next(s for s in signals if s["name"] == "rsi_14")
        assert rsi_sig["direction"] == "bearish"

    def test_macd_positive(self) -> None:
        data = {"indicators": {"macd_histogram": 1.5}}
        signals = _extract_technical(data)
        macd_sig = next(s for s in signals if s["name"] == "macd_histogram")
        assert macd_sig["direction"] == "bullish"

    def test_macd_negative(self) -> None:
        data = {"indicators": {"macd_histogram": -2.0}}
        signals = _extract_technical(data)
        macd_sig = next(s for s in signals if s["name"] == "macd_histogram")
        assert macd_sig["direction"] == "bearish"

    def test_sma_positions(self) -> None:
        data = {
            "price_vs_sma20": "above",
            "price_vs_sma50": "below",
            "indicators": {"macd_histogram": 0},
        }
        signals = _extract_technical(data)
        sma20 = next(s for s in signals if s["name"] == "price_vs_sma20")
        sma50 = next(s for s in signals if s["name"] == "price_vs_sma50")
        assert sma20["direction"] == "bullish"
        assert sma50["direction"] == "bearish"

    def test_bb_below_lower(self) -> None:
        data = {
            "current_price": 120.0,
            "indicators": {
                "macd_histogram": 0,
                "bb_lower": 130.0,
                "bb_upper": 160.0,
            },
        }
        signals = _extract_technical(data)
        bb = next(s for s in signals if s["name"] == "bb_position")
        assert bb["direction"] == "bullish"

    def test_bb_above_upper(self) -> None:
        data = {
            "current_price": 170.0,
            "indicators": {
                "macd_histogram": 0,
                "bb_lower": 130.0,
                "bb_upper": 160.0,
            },
        }
        signals = _extract_technical(data)
        bb = next(s for s in signals if s["name"] == "bb_position")
        assert bb["direction"] == "bearish"

    def test_full_indicators(self, sample_market_data: dict) -> None:
        signals = _extract_technical(sample_market_data)
        names = {s["name"] for s in signals}
        assert "rsi_14" in names
        assert "macd_histogram" in names
        assert all(s["source"] == "technical" for s in signals)


class TestExtractOnchain:
    """Test _extract_onchain with real and stub data."""

    def test_stub_data_returns_empty(self) -> None:
        assert _extract_onchain({"source": "stub"}) == []

    def test_tvl_rising(self) -> None:
        data = {"defillama": {"solana_tvl_change_7d": 10.0}}
        signals = _extract_onchain(data)
        tvl = next(s for s in signals if s["name"] == "tvl_trend")
        assert tvl["direction"] == "bullish"

    def test_tvl_falling(self) -> None:
        data = {"defillama": {"solana_tvl_change_7d": -8.0}}
        signals = _extract_onchain(data)
        tvl = next(s for s in signals if s["name"] == "tvl_trend")
        assert tvl["direction"] == "bearish"

    def test_whale_activity_high(self) -> None:
        data = {
            "solana_network": {
                "whale_activity": {"whale_activity_level": "high"},
            },
        }
        signals = _extract_onchain(data)
        whale = next(s for s in signals if s["name"] == "whale_activity")
        assert whale["direction"] == "bullish"

    def test_whale_activity_low(self) -> None:
        data = {
            "solana_network": {
                "whale_activity": {"whale_activity_level": "low"},
            },
        }
        signals = _extract_onchain(data)
        whale = next(s for s in signals if s["name"] == "whale_activity")
        assert whale["direction"] == "bearish"

    def test_dex_volume_change(self, sample_onchain_data: dict) -> None:
        signals = _extract_onchain(sample_onchain_data)
        dex = next(s for s in signals if s["name"] == "dex_volume")
        assert dex["direction"] == "bullish"


class TestExtractSentiment:
    """Test _extract_sentiment."""

    def test_extreme_fear_is_bullish(self) -> None:
        state = {"fear_greed_index": 10}
        signals = _extract_sentiment(state)
        fng = next(s for s in signals if s["name"] == "fear_greed")
        assert fng["direction"] == "bullish"

    def test_extreme_greed_is_bearish(self) -> None:
        state = {"fear_greed_index": 90}
        signals = _extract_sentiment(state)
        fng = next(s for s in signals if s["name"] == "fear_greed")
        assert fng["direction"] == "bearish"

    def test_reddit_bullish_keyword(self) -> None:
        state = {
            "fear_greed_index": 50,
            "sentiment_report": "Community is bullish on SOL.",
        }
        signals = _extract_sentiment(state)
        reddit = next(s for s in signals if s["name"] == "reddit_sentiment")
        assert reddit["direction"] == "bullish"

    def test_reddit_bearish_keyword(self) -> None:
        state = {
            "fear_greed_index": 50,
            "sentiment_report": "Market is bearish. Sell pressure increasing.",
        }
        signals = _extract_sentiment(state)
        reddit = next(s for s in signals if s["name"] == "reddit_sentiment")
        assert reddit["direction"] == "bearish"


class TestExtractMacro:
    """Test _extract_macro."""

    def test_risk_on(self) -> None:
        state = {"macro_regime": "risk_on", "market_regime": "bull", "regime_confidence": 8}
        signals = _extract_macro(state)
        macro = next(s for s in signals if s["name"] == "macro_regime")
        assert macro["direction"] == "bullish"

    def test_risk_off(self) -> None:
        state = {"macro_regime": "risk_off", "market_regime": "bear", "regime_confidence": 7}
        signals = _extract_macro(state)
        macro = next(s for s in signals if s["name"] == "macro_regime")
        assert macro["direction"] == "bearish"

    def test_unknown_macro_skipped(self) -> None:
        state = {"macro_regime": "unknown", "market_regime": "unknown"}
        signals = _extract_macro(state)
        assert not any(s["name"] == "macro_regime" for s in signals)
        assert not any(s["name"] == "market_regime" for s in signals)


class TestExtractBrain:
    """Test _extract_brain."""

    def test_buy_decision(self) -> None:
        brain = json.dumps({"action": "BUY", "confidence": 8, "size_pct": 15, "regime": "bull"})
        signals = _extract_brain({"brain_decision": brain})
        action_sig = next(s for s in signals if s["name"] == "brain_action")
        assert action_sig["direction"] == "bullish"
        assert len(signals) == 4  # action, confidence, size_pct, regime

    def test_sell_decision(self) -> None:
        brain = json.dumps({"action": "SELL", "confidence": 6, "size_pct": 20, "regime": "bear"})
        signals = _extract_brain({"brain_decision": brain})
        action_sig = next(s for s in signals if s["name"] == "brain_action")
        assert action_sig["direction"] == "bearish"

    def test_hold_decision(self) -> None:
        brain = json.dumps({"action": "HOLD", "confidence": 3})
        signals = _extract_brain({"brain_decision": brain})
        action_sig = next(s for s in signals if s["name"] == "brain_action")
        assert action_sig["direction"] == "neutral"

    def test_invalid_json_returns_empty(self) -> None:
        assert _extract_brain({"brain_decision": "not json"}) == []

    def test_empty_brain_returns_empty(self) -> None:
        assert _extract_brain({"brain_decision": ""}) == []
        assert _extract_brain({}) == []


class TestExtractSignals:
    """Test the top-level extract_signals orchestrator."""

    def test_full_state_produces_signals(self, sample_agent_state: dict) -> None:
        signals = extract_signals(sample_agent_state)
        assert len(signals) > 5
        sources = {s["source"] for s in signals}
        assert "technical" in sources
        assert "onchain" in sources
        assert "sentiment" in sources
        assert "brain" in sources

    def test_empty_state_still_works(self) -> None:
        signals = extract_signals({})
        # At minimum fear_greed defaults to 50 → neutral signal
        assert isinstance(signals, list)

    def test_all_signals_have_required_keys(self, sample_agent_state: dict) -> None:
        for sig in extract_signals(sample_agent_state):
            assert "name" in sig
            assert "source" in sig
            assert "direction" in sig
            assert sig["direction"] in ("bullish", "bearish", "neutral")
            assert "confidence" in sig
            assert 0 <= sig["confidence"] <= 1.0
