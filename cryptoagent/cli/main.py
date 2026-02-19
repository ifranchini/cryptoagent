"""CLI entry point for CryptoAgent."""

from __future__ import annotations

import json
import logging
import os
import sys
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from cryptoagent.config import AgentConfig
from cryptoagent.graph.builder import TradingGraph

app = typer.Typer(name="cryptoagent", help="Multi-agent LLM trading system", invoke_without_command=True)
console = Console()


def _setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    # Quiet noisy libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("litellm").setLevel(logging.WARNING)
    logging.getLogger("ccxt").setLevel(logging.WARNING)


@app.command()
def analyze(
    token: str = typer.Argument("SOL", help="Token to analyze (e.g., SOL, BTC, ETH)"),
    asset_type: str = typer.Option("crypto", "--asset-type", "-a", help="Asset type: crypto or equity"),
    brain_model: Optional[str] = typer.Option(None, "--brain-model", help="LLM model for Brain agent"),
    research_model: Optional[str] = typer.Option(None, "--research-model", help="LLM model for Research agent"),
    sentiment_model: Optional[str] = typer.Option(None, "--sentiment-model", help="LLM model for Sentiment agent"),
    trader_model: Optional[str] = typer.Option(None, "--trader-model", help="LLM model for Trader agent"),
    capital: float = typer.Option(10000.0, "--capital", "-c", help="Initial capital in USD"),
    exchange: str = typer.Option("binance", "--exchange", "-e", help="Exchange for market data"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging"),
) -> None:
    """Run the full trading analysis pipeline for a token."""
    _setup_logging(verbose)

    # Apply CLI overrides to env before config loads
    if brain_model:
        os.environ["CA_BRAIN_MODEL"] = brain_model
    if research_model:
        os.environ["CA_RESEARCH_MODEL"] = research_model
    if sentiment_model:
        os.environ["CA_SENTIMENT_MODEL"] = sentiment_model
    if trader_model:
        os.environ["CA_TRADER_MODEL"] = trader_model
    if asset_type:
        os.environ["CA_ASSET_TYPE"] = asset_type
    if exchange:
        os.environ["CA_EXCHANGE"] = exchange

    config = AgentConfig(initial_capital=capital)

    # Display config
    console.print(Panel.fit(
        f"[bold]Token:[/bold] {token.upper()}\n"
        f"[bold]Asset Type:[/bold] {config.asset_type}\n"
        f"[bold]Exchange:[/bold] {config.exchange}\n"
        f"[bold]Capital:[/bold] ${config.initial_capital:,.2f}\n"
        f"[bold]Mode:[/bold] {config.execution_mode}\n"
        f"\n[bold]Models:[/bold]\n"
        f"  Research:  {config.research_model}\n"
        f"  Sentiment: {config.sentiment_model}\n"
        f"  Brain:     {config.brain_model}\n"
        f"  Trader:    {config.trader_model}",
        title="CryptoAgent",
        border_style="blue",
    ))

    # Run pipeline
    console.print("\n[bold yellow]Running analysis pipeline...[/bold yellow]\n")

    try:
        graph = TradingGraph(config=config)
        result = graph.run(token=token)
    except Exception as e:
        console.print(f"\n[bold red]Pipeline failed:[/bold red] {e}")
        if verbose:
            console.print_exception()
        sys.exit(1)

    # Display results
    _display_results(result, token)


def _display_results(result: dict, token: str) -> None:
    """Pretty-print pipeline results."""
    # Research report
    console.print(Panel(
        result.get("research_report", "No report"),
        title="Research Agent Report",
        border_style="green",
    ))

    # Sentiment report
    console.print(Panel(
        result.get("sentiment_report", "No report"),
        title="Sentiment Agent Report",
        border_style="cyan",
    ))

    # Brain decision
    brain_raw = result.get("brain_decision", "{}")
    try:
        decision = json.loads(brain_raw)
    except json.JSONDecodeError:
        decision = {"raw": brain_raw}

    decision_table = Table(title="Brain Decision", border_style="magenta")
    decision_table.add_column("Field", style="bold")
    decision_table.add_column("Value")
    for key, value in decision.items():
        decision_table.add_row(str(key), str(value))
    console.print(decision_table)

    # Trade result
    trade_raw = result.get("trade_result", "{}")
    try:
        trade = json.loads(trade_raw)
    except json.JSONDecodeError:
        trade = {"raw": trade_raw}

    executed = trade.get("executed", False)
    status = "[bold green]EXECUTED[/bold green]" if executed else "[bold yellow]NOT EXECUTED[/bold yellow]"
    console.print(f"\nTrade Status: {status}")

    if executed and "execution" in trade:
        exec_info = trade["execution"]
        if exec_info.get("success"):
            t = exec_info.get("trade", {})
            console.print(
                f"  Action: {t.get('action')} {t.get('quantity', 0):.4f} {token.upper()} "
                f"@ ${t.get('price', 0):,.2f}"
            )
        portfolio = exec_info.get("updated_portfolio", {})
        if portfolio:
            console.print(f"  Cash: ${portfolio.get('cash', 0):,.2f}")
            console.print(f"  Holdings: {portfolio.get('holdings', {})}")
            console.print(f"  Net Worth: ${portfolio.get('net_worth', 0):,.2f}")
    elif not executed:
        console.print(f"  Reason: {trade.get('reason', trade.get('validation', {}).get('reason', 'N/A'))}")


def main() -> None:
    """Entry point."""
    app()


if __name__ == "__main__":
    main()
