"""Unit tests for the Risk Sentinel pre/post checks."""

from __future__ import annotations


from cryptoagent.risk.sentinel import RiskSentinel


class TestPreCheck:
    """RiskSentinel.pre_check tests."""

    def test_normal_portfolio_proceeds(self) -> None:
        sentinel = RiskSentinel(initial_capital=10000.0)
        portfolio = {"net_worth": 9500.0, "cash": 5000.0}
        result = sentinel.pre_check(portfolio, daily_pnl=0.0)
        assert result["verdict"] == "proceed"
        assert result["reasons"] == []

    def test_daily_loss_exceeds_limit(self) -> None:
        sentinel = RiskSentinel(max_daily_loss_pct=5.0, initial_capital=10000.0)
        portfolio = {"net_worth": 9500.0}
        # daily PnL = -500 on net_worth 9500 → 5.3% loss
        result = sentinel.pre_check(portfolio, daily_pnl=-500.0)
        assert result["verdict"] == "halt"
        assert any("Daily loss" in r for r in result["reasons"])

    def test_daily_loss_below_limit(self) -> None:
        sentinel = RiskSentinel(max_daily_loss_pct=5.0, initial_capital=10000.0)
        portfolio = {"net_worth": 9500.0}
        # daily PnL = -100 on net_worth 9500 → 1.1% loss
        result = sentinel.pre_check(portfolio, daily_pnl=-100.0)
        assert result["verdict"] == "proceed"

    def test_drawdown_exceeds_limit(self) -> None:
        sentinel = RiskSentinel(max_drawdown_pct=15.0, initial_capital=10000.0)
        portfolio = {"net_worth": 8000.0}
        # drawdown = (1 - 8000/10000) * 100 = 20%
        result = sentinel.pre_check(portfolio, daily_pnl=0.0)
        assert result["verdict"] == "halt"
        assert "Drawdown" in result["reasons"][0]

    def test_drawdown_within_limit(self) -> None:
        sentinel = RiskSentinel(max_drawdown_pct=15.0, initial_capital=10000.0)
        portfolio = {"net_worth": 9000.0}
        # drawdown = 10%
        result = sentinel.pre_check(portfolio, daily_pnl=0.0)
        assert result["verdict"] == "proceed"

    def test_both_triggers_halt_with_two_reasons(self) -> None:
        sentinel = RiskSentinel(
            max_daily_loss_pct=3.0,
            max_drawdown_pct=10.0,
            initial_capital=10000.0,
        )
        portfolio = {"net_worth": 8500.0, "cash": 8500.0}
        result = sentinel.pre_check(portfolio, daily_pnl=-400.0)
        assert result["verdict"] == "halt"
        assert len(result["reasons"]) == 2

    def test_zero_net_worth(self) -> None:
        sentinel = RiskSentinel(initial_capital=10000.0)
        portfolio = {"net_worth": 0}
        result = sentinel.pre_check(portfolio, daily_pnl=-100.0)
        # net_worth=0 → daily_pnl check skipped (division guard), drawdown = 100%
        assert result["verdict"] == "halt"

    def test_positive_pnl_never_halts(self) -> None:
        sentinel = RiskSentinel(max_daily_loss_pct=1.0, initial_capital=10000.0)
        result = sentinel.pre_check({"net_worth": 12000.0}, daily_pnl=500.0)
        assert result["verdict"] == "proceed"

    def test_custom_thresholds(self) -> None:
        sentinel = RiskSentinel(
            max_daily_loss_pct=1.0,
            max_drawdown_pct=5.0,
            initial_capital=5000.0,
        )
        portfolio = {"net_worth": 4800.0}
        # drawdown = 4%, below 5%
        result = sentinel.pre_check(portfolio, daily_pnl=0.0)
        assert result["verdict"] == "proceed"

        portfolio = {"net_worth": 4700.0}
        # drawdown = 6%, above 5%
        result = sentinel.pre_check(portfolio, daily_pnl=0.0)
        assert result["verdict"] == "halt"


class TestPostCheck:
    """RiskSentinel.post_check tests."""

    def test_hold_action_proceeds(self, sample_market_data: dict) -> None:
        sentinel = RiskSentinel()
        result = sentinel.post_check(
            brain_decision={"action": "HOLD", "size_pct": 0},
            portfolio={"net_worth": 10000.0, "cash": 5000.0},
            market_data=sample_market_data,
        )
        assert result["verdict"] == "proceed"

    def test_normal_buy_proceeds(self, sample_market_data: dict) -> None:
        sentinel = RiskSentinel()
        result = sentinel.post_check(
            brain_decision={"action": "BUY", "size_pct": 10},
            portfolio={"net_worth": 10000.0, "cash": 5000.0},
            market_data=sample_market_data,
        )
        assert result["verdict"] == "proceed"

    def test_atr_spike_halves_position(self) -> None:
        sentinel = RiskSentinel(volatility_spike_multiplier=2.0)
        market_data = {
            "current_price": 100.0,
            "indicators": {"atr_14": 20.0},  # 20% of price >> 2.0*2.5=5%
        }
        result = sentinel.post_check(
            brain_decision={"action": "BUY", "size_pct": 20},
            portfolio={"net_worth": 10000.0, "cash": 5000.0},
            market_data=market_data,
        )
        assert result["verdict"] == "reduce"
        assert result["modified_size_pct"] == 10.0
        assert any("ATR spike" in r for r in result["reasons"])

    def test_excessive_concentration_capped(self) -> None:
        sentinel = RiskSentinel()
        result = sentinel.post_check(
            brain_decision={"action": "BUY", "size_pct": 80},
            portfolio={"net_worth": 10000.0, "cash": 10000.0},
            market_data={"current_price": 100.0, "indicators": {}},
        )
        assert result["verdict"] == "reduce"
        assert result["modified_size_pct"] <= 25

    def test_both_atr_and_concentration(self) -> None:
        sentinel = RiskSentinel(volatility_spike_multiplier=2.0)
        market_data = {
            "current_price": 100.0,
            "indicators": {"atr_14": 20.0},
        }
        result = sentinel.post_check(
            brain_decision={"action": "BUY", "size_pct": 80},
            portfolio={"net_worth": 10000.0, "cash": 10000.0},
            market_data=market_data,
        )
        assert result["verdict"] == "reduce"
        assert len(result["reasons"]) == 2

    def test_sell_action_skips_concentration(self) -> None:
        sentinel = RiskSentinel()
        result = sentinel.post_check(
            brain_decision={"action": "SELL", "size_pct": 50},
            portfolio={"net_worth": 10000.0, "cash": 2000.0},
            market_data={"current_price": 100.0, "indicators": {}},
        )
        # Concentration check only applies to BUY
        assert result["verdict"] == "proceed"
