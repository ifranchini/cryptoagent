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

    # Persistence
    db_path: str = "data/cryptoagent.db"

    # Reflection
    reflection_model: str = "openai/gpt-4o-mini"
    reflection_cycle_length: int = 5  # Generate Level 2 every N cycles

    # Risk management
    max_daily_loss_pct: float = 5.0
    max_drawdown_pct: float = 15.0
    volatility_spike_multiplier: float = 2.0

    # On-chain data
    solana_rpc_url: str = "https://api.mainnet-beta.solana.com"
    defillama_base_url: str = "https://api.llama.fi"

    # Social sentiment
    twitter_bearer_token: str = ""
    twitter_scrape_url: str = ""
    reddit_subreddits: list[str] = ["solana", "cryptocurrency"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="CA_",
        case_sensitive=False,
        extra="ignore",
    )
