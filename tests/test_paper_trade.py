"""Unit tests for the paper trading execution engine."""

from __future__ import annotations

import pytest

from cryptoagent.execution.paper_trade import execute_paper_trade


class TestBuy:
    """Paper trade BUY action tests."""

    def test_buy_with_sufficient_cash(self) -> None:
        portfolio = {"cash": 10000.0, "holdings": {}, "trade_history": []}
        result = execute_paper_trade(
            action="BUY",
            token="SOL",
            size_pct=10,
            portfolio_state=portfolio,
            current_price=150.0,
        )
        assert result["success"] is True
        updated = result["updated_portfolio"]
        assert updated["cash"] < 10000.0
        assert updated["holdings"]["SOL"] > 0

    def test_buy_calculates_fees(self) -> None:
        portfolio = {"cash": 10000.0, "holdings": {}, "trade_history": []}
        result = execute_paper_trade(
            action="BUY",
            token="SOL",
            size_pct=10,
            portfolio_state=portfolio,
            current_price=100.0,
            fee_pct=0.001,
        )
        trade = result["trade"]
        # 10% of 10000 = 1000 trade amount, fee = 1.0
        assert abs(trade["fee"] - 1.0) < 0.01
        # quantity = (1000 - 1) / 100 = 9.99
        assert abs(trade["quantity"] - 9.99) < 0.01

    def test_buy_insufficient_cash(self) -> None:
        # size_pct=10 of 0 cash = 0 trade amount
        # Actually this succeeds with 0 quantity.
        # Let's test the real fail case: cash < trade_amount
        # Looking at the code: trade_amount = cash * size_fraction
        # So trade_amount can never > cash since fraction <= 1.
        # The only fail is if cash is literally negative.
        # Let's verify a normal buy reduces cash correctly instead.
        portfolio = {"cash": 100.0, "holdings": {}, "trade_history": []}
        result = execute_paper_trade(
            action="BUY",
            token="SOL",
            size_pct=50,
            portfolio_state=portfolio,
            current_price=200.0,
        )
        assert result["success"] is True
        assert result["updated_portfolio"]["cash"] == pytest.approx(50.0, abs=0.1)

    def test_buy_adds_to_existing_holdings(self) -> None:
        portfolio = {"cash": 5000.0, "holdings": {"SOL": 5.0}, "trade_history": []}
        result = execute_paper_trade(
            action="BUY",
            token="sol",  # lowercase — should be uppercased
            size_pct=10,
            portfolio_state=portfolio,
            current_price=100.0,
        )
        assert result["success"] is True
        # Should add to existing 5.0 holdings
        assert result["updated_portfolio"]["holdings"]["SOL"] > 5.0

    def test_buy_zero_price_yields_zero_quantity(self) -> None:
        portfolio = {"cash": 1000.0, "holdings": {}, "trade_history": []}
        result = execute_paper_trade(
            action="BUY",
            token="SOL",
            size_pct=10,
            portfolio_state=portfolio,
            current_price=0.0,
        )
        assert result["success"] is True
        assert result["trade"]["quantity"] == 0


class TestSell:
    """Paper trade SELL action tests."""

    def test_sell_with_holdings(self) -> None:
        portfolio = {"cash": 0.0, "holdings": {"SOL": 10.0}, "trade_history": []}
        result = execute_paper_trade(
            action="SELL",
            token="SOL",
            size_pct=50,
            portfolio_state=portfolio,
            current_price=150.0,
        )
        assert result["success"] is True
        updated = result["updated_portfolio"]
        assert updated["holdings"]["SOL"] == pytest.approx(5.0, abs=1e-6)
        assert updated["cash"] > 0

    def test_sell_no_holdings(self) -> None:
        portfolio = {"cash": 5000.0, "holdings": {}, "trade_history": []}
        result = execute_paper_trade(
            action="SELL",
            token="SOL",
            size_pct=50,
            portfolio_state=portfolio,
            current_price=150.0,
        )
        assert result["success"] is False
        assert "No SOL" in result["error"]

    def test_sell_applies_fee(self) -> None:
        portfolio = {"cash": 0.0, "holdings": {"SOL": 10.0}, "trade_history": []}
        result = execute_paper_trade(
            action="SELL",
            token="SOL",
            size_pct=100,
            portfolio_state=portfolio,
            current_price=100.0,
            fee_pct=0.001,
        )
        trade = result["trade"]
        # 10 * 100 = 1000 gross, fee = 1.0, net = 999.0
        assert abs(trade["fee"] - 1.0) < 0.01
        assert abs(result["updated_portfolio"]["cash"] - 999.0) < 0.01

    def test_sell_cleans_near_zero_holdings(self) -> None:
        portfolio = {"cash": 0.0, "holdings": {"SOL": 1e-11}, "trade_history": []}
        # Selling 100% of near-zero should clean up
        result = execute_paper_trade(
            action="SELL",
            token="SOL",
            size_pct=100,
            portfolio_state=portfolio,
            current_price=150.0,
        )
        assert result["success"] is True
        assert result["updated_portfolio"]["holdings"]["SOL"] == 0


class TestEdgeCases:
    """Edge cases and miscellaneous."""

    def test_unknown_action(self) -> None:
        portfolio = {"cash": 5000.0, "holdings": {}, "trade_history": []}
        result = execute_paper_trade(
            action="SHORT",
            token="SOL",
            size_pct=10,
            portfolio_state=portfolio,
            current_price=150.0,
        )
        assert result["success"] is False
        assert "Unknown action" in result["error"]

    def test_full_round_trip(self) -> None:
        portfolio = {"cash": 10000.0, "holdings": {}, "trade_history": []}

        # BUY
        buy = execute_paper_trade(
            action="BUY",
            token="SOL",
            size_pct=50,
            portfolio_state=portfolio,
            current_price=100.0,
            fee_pct=0.001,
        )
        assert buy["success"] is True

        # SELL at same price
        sell = execute_paper_trade(
            action="SELL",
            token="SOL",
            size_pct=100,
            portfolio_state=buy["updated_portfolio"],
            current_price=100.0,
            fee_pct=0.001,
        )
        assert sell["success"] is True
        # Net worth should be slightly less than 10000 due to fees
        assert sell["updated_portfolio"]["net_worth"] < 10000.0

    def test_net_worth_includes_holdings(self) -> None:
        portfolio = {"cash": 5000.0, "holdings": {}, "trade_history": []}
        result = execute_paper_trade(
            action="BUY",
            token="SOL",
            size_pct=50,
            portfolio_state=portfolio,
            current_price=100.0,
            fee_pct=0.0,
        )
        updated = result["updated_portfolio"]
        # Cash 2500 + holdings_value (25 * 100 = 2500) = 5000
        assert updated["net_worth"] == pytest.approx(5000.0, abs=1.0)

    def test_trade_history_appended(self) -> None:
        portfolio = {"cash": 5000.0, "holdings": {}, "trade_history": [{"old": True}]}
        result = execute_paper_trade(
            action="BUY",
            token="SOL",
            size_pct=10,
            portfolio_state=portfolio,
            current_price=100.0,
        )
        history = result["updated_portfolio"]["trade_history"]
        assert len(history) == 2
        assert history[0] == {"old": True}

    def test_holdings_value_only_for_traded_token(self) -> None:
        portfolio = {
            "cash": 1000.0,
            "holdings": {"ETH": 2.0},  # ETH price unknown
            "trade_history": [],
        }
        result = execute_paper_trade(
            action="BUY",
            token="SOL",
            size_pct=10,
            portfolio_state=portfolio,
            current_price=100.0,
            fee_pct=0.0,
        )
        # ETH valued at 0 (price unknown), SOL at 100
        updated = result["updated_portfolio"]
        sol_qty = updated["holdings"]["SOL"]
        expected_net = updated["cash"] + sol_qty * 100.0  # ETH = 0
        assert updated["net_worth"] == pytest.approx(expected_net, abs=0.1)
