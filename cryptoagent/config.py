"""Application configuration via Pydantic settings."""

from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class AgentConfig(BaseSettings):
    """CryptoAgent configuration. All fields can be set via env vars with CA_ prefix."""

    # Per-agent LLM models (LiteLLM model strings)
    research_model: str = "openai/gpt-4o-mini"
    sentiment_model: str = "openai/gpt-4o-mini"
    brain_model: str = "openai/gpt-4o"
    trader_model: str = "openai/gpt-4o-mini"

    # Asset
    asset_type: Literal["crypto", "equity"] = "crypto"
    target_token: str = "SOL"
    exchange: str = "binance"

    # Execution
    execution_mode: Literal["paper", "live"] = "paper"
    initial_capital: float = 10000.0

    # Trading defaults
    max_position_pct: float = 0.25  # Max 25% of portfolio in one trade
    trading_fee_pct: float = 0.001  # 0.1% fee

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="CA_",
        case_sensitive=False,
        extra="ignore",
    )
