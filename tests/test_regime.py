"""Unit tests for the market regime classifier."""

from __future__ import annotations


from cryptoagent.dataflows.regime import classify


class TestClassify:
    """Test regime classification from technical indicators."""

    def test_bull_regime(self) -> None:
        result = classify({
            "current_price": 160.0,
            "sma_50": 140.0,
            "rsi_14": 65.0,
            "macd_histogram": 2.0,
            "atr_14": 5.0,
            "sma_20": 150.0,
        })
        assert result["regime"] == "bull"
        assert result["confidence"] >= 7

    def test_bear_regime(self) -> None:
        result = classify({
            "current_price": 100.0,
            "sma_50": 140.0,
            "rsi_14": 35.0,
            "macd_histogram": -3.0,
            "atr_14": 8.0,
            "sma_20": 120.0,
        })
        assert result["regime"] == "bear"

    def test_sideways_regime(self) -> None:
        # 2 of 4 bullish signals → sideways
        result = classify({
            "current_price": 145.0,
            "sma_50": 140.0,   # above → bullish
            "rsi_14": 45.0,    # below 50 → bearish
            "macd_histogram": 0.5,  # positive → bullish
            "atr_14": 2.0,     # low ATR
            "sma_20": 150.0,   # below → bearish
        })
        assert result["regime"] == "sideways"

    def test_insufficient_data(self) -> None:
        result = classify({})
        assert result["regime"] == "unknown"
        assert result["confidence"] == 1

    def test_missing_sma50(self) -> None:
        result = classify({"current_price": 100.0})
        assert result["regime"] == "unknown"

    def test_rsi_extreme_boosts_confidence(self) -> None:
        # Bull with RSI > 70 → confidence boost
        result = classify({
            "current_price": 160.0,
            "sma_50": 140.0,
            "rsi_14": 75.0,
            "macd_histogram": 2.0,
            "atr_14": 5.0,
            "sma_20": 150.0,
        })
        assert result["regime"] == "bull"
        assert result["confidence"] >= 8

    def test_bear_rsi_extreme_boosts_confidence(self) -> None:
        result = classify({
            "current_price": 100.0,
            "sma_50": 140.0,
            "rsi_14": 25.0,
            "macd_histogram": -3.0,
            "atr_14": 8.0,
            "sma_20": 120.0,
        })
        assert result["regime"] == "bear"
        # Bear confidence boosted by RSI < 30
        assert result["confidence"] >= 8

    def test_signals_dict_populated(self) -> None:
        result = classify({
            "current_price": 150.0,
            "sma_50": 140.0,
            "rsi_14": 55.0,
            "macd_histogram": 1.0,
            "atr_14": 4.0,
            "sma_20": 145.0,
        })
        signals = result["signals"]
        assert "price_above_sma50" in signals
        assert "rsi_above_50" in signals
        assert "macd_positive" in signals
        assert "rsi_value" in signals
