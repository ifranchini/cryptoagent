"""Paper trading environment — simulates trade execution without real money."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


def execute_paper_trade(
    action: str,
    token: str,
    size_pct: float,
    portfolio_state: dict,
    current_price: float,
    fee_pct: float = 0.001,
) -> dict:
    """Execute a paper trade and return updated portfolio state.

    Args:
        action: "BUY" or "SELL"
        token: Token symbol (e.g., "SOL")
        size_pct: Percentage of available capital to trade (0-100)
        portfolio_state: Current portfolio dict
        current_price: Current market price
        fee_pct: Trading fee as decimal (0.001 = 0.1%)

    Returns:
        Dict with trade details and updated portfolio.
    """
    cash = float(portfolio_state.get("cash", 0))
    holdings = dict(portfolio_state.get("holdings", {}))
    trade_history = list(portfolio_state.get("trade_history", []))

    token = token.upper()
    size_fraction = size_pct / 100.0

    trade_record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "action": action,
        "token": token,
        "price": current_price,
        "size_pct": size_pct,
    }

    if action == "BUY":
        trade_amount = cash * size_fraction
        fee = trade_amount * fee_pct
        net_amount = trade_amount - fee
        quantity = net_amount / current_price if current_price > 0 else 0

        if trade_amount > cash:
            return {
                "success": False,
                "error": f"Insufficient cash: need ${trade_amount:.2f}, have ${cash:.2f}",
            }

        cash -= trade_amount
        holdings[token] = holdings.get(token, 0) + quantity

        trade_record.update({
            "quantity": quantity,
            "cost": trade_amount,
            "fee": fee,
        })

        logger.info(
            "[Paper Trade] BUY %.4f %s @ $%.2f (cost: $%.2f, fee: $%.2f)",
            quantity, token, current_price, trade_amount, fee,
        )

    elif action == "SELL":
        current_holdings = holdings.get(token, 0)
        if current_holdings <= 0:
            return {
                "success": False,
                "error": f"No {token} holdings to sell",
            }

        sell_quantity = current_holdings * size_fraction
        gross_proceeds = sell_quantity * current_price
        fee = gross_proceeds * fee_pct
        net_proceeds = gross_proceeds - fee

        holdings[token] = current_holdings - sell_quantity
        if holdings[token] < 1e-10:
            holdings[token] = 0
        cash += net_proceeds

        trade_record.update({
            "quantity": sell_quantity,
            "proceeds": net_proceeds,
            "fee": fee,
        })

        logger.info(
            "[Paper Trade] SELL %.4f %s @ $%.2f (proceeds: $%.2f, fee: $%.2f)",
            sell_quantity, token, current_price, net_proceeds, fee,
        )
    else:
        return {"success": False, "error": f"Unknown action: {action}"}

    # Calculate net worth
    holdings_value = sum(
        qty * current_price if tok == token else qty * 0  # Only current token price known
        for tok, qty in holdings.items()
    )
    net_worth = cash + holdings_value

    trade_history.append(trade_record)

    updated_portfolio = {
        "cash": round(cash, 2),
        "holdings": {k: round(v, 8) for k, v in holdings.items()},
        "net_worth": round(net_worth, 2),
        "trade_history": trade_history,
    }

    return {
        "success": True,
        "trade": trade_record,
        "updated_portfolio": updated_portfolio,
    }
