# CryptoAgent

Multi-agent LLM trading system. 5 specialized agents collaborate to analyze markets and execute paper trades, each powered by a different LLM suited to its role.

## Architecture

```
DATA LAYER (CCXT + DeFiLlama + Solana RPC + Reddit + X/Twitter + Fear & Greed + FRED + CryptoPanic)
        │
  ┌─────┼─────┐
  ▼     ▼     ▼
Research Sentiment Macro  ← cheap/fast LLMs (parallel)
  │     │     │
  └─────┼─────┘
        ▼
      Brain                ← best reasoning LLM (+ regime, on-chain, macro, reflections)
        │
        ▼
      Trader               ← fast LLM → paper/live execution
```

**Pre-pipeline:** Risk Sentinel pre-check, market regime classification, cross-trial reflection loading.
**Post-pipeline:** Risk Sentinel post-check, trade logging (SQLite), Level 1/2 reflection generation.

| Agent | Role | Default Model |
|-------|------|---------------|
| **Research** | Market data + TA indicators + on-chain (DeFiLlama, Solana RPC) + macro | `deepseek/deepseek-chat-v3-0324` |
| **Sentiment** | Reddit posts, X/Twitter sentiment, Fear & Greed Index, crypto news | `deepseek/deepseek-chat-v3-0324` |
| **Macro** | FRED macro data (M2, Fed rate, yields, yield curve), macro regime | `deepseek/deepseek-chat-v3-0324` |
| **Brain** | Regime-aware signal weighting, on-chain + macro + cross-trial reflections, trade decision | `anthropic/claude-sonnet-4` |
| **Trader** | Execution validation, order routing, paper trading | `deepseek/deepseek-chat-v3-0324` |

## Key Design Choices

- **Model-agnostic** — [LiteLLM](https://github.com/BerriAI/litellm) as unified gateway. Supports 100+ providers (OpenAI, Anthropic, DeepSeek, Ollama, OpenRouter, etc.). Each agent can use a different model.
- **LangGraph orchestration** — Research + Sentiment + Macro run in parallel, all three feed into Brain, then Trader executes. Clean 5-node DAG.
- **Real on-chain data** — DeFiLlama (TVL, DEX volume, fees) + Solana RPC (TPS, whale activity). Graceful degradation to stubs on API failure.
- **Real social sentiment** — Reddit JSON API (r/solana, r/cryptocurrency) + X/Twitter (scraping proxy or official API v2). Fear & Greed Index from Alternative.me.
- **Two-level reflection memory** — Level 1 (per-cycle lessons) + Level 2 (cross-trial strategic reviews). Stored in SQLite, injected into Brain prompt.
- **Risk Sentinel** — Pre/post pipeline threshold checks (daily loss, drawdown, volatility spikes). Can halt trading or reduce position sizes.
- **Market regime detector** — Pure numeric heuristic (price vs SMA50, RSI, MACD histogram). Regime + confidence fed to Brain.
- **FS-ReasoningAgent pattern** — Research labels findings as `[FACT]` vs `[INFERENCE]`. Brain weights factual signals more heavily in bearish/uncertain regimes.

## Quick Start

```bash
# Install
cd cryptoagent
uv sync

# Configure (need at least one LLM provider key)
cp .env.example .env
# Edit .env — set your API key(s) and model preferences

# Single cycle
uv run python -m cryptoagent.cli.main SOL

# Multi-cycle with portfolio carry-forward
uv run python -m cryptoagent.cli.main SOL --cycles 6
```

## Configuration

All settings via environment variables (prefix `CA_`) or `.env` file:

```bash
# Per-agent models (any LiteLLM model string)
CA_RESEARCH_MODEL=openrouter/deepseek/deepseek-chat-v3-0324
CA_SENTIMENT_MODEL=openrouter/deepseek/deepseek-chat-v3-0324
CA_BRAIN_MODEL=openrouter/anthropic/claude-sonnet-4
CA_TRADER_MODEL=openrouter/deepseek/deepseek-chat-v3-0324
CA_MACRO_MODEL=openrouter/deepseek/deepseek-chat-v3-0324

# Macro data (free at https://fred.stlouisfed.org/docs/api/api_key.html)
CA_FRED_API_KEY=your_fred_api_key_here

# Asset & execution
CA_TARGET_TOKEN=SOL
CA_EXCHANGE=binance
CA_EXECUTION_MODE=paper
CA_INITIAL_CAPITAL=10000.0

# Persistence
CA_DB_PATH=data/cryptoagent.db

# Reflection
CA_REFLECTION_MODEL=openrouter/deepseek/deepseek-chat-v3-0324
CA_REFLECTION_CYCLE_LENGTH=5

# Risk management
CA_MAX_DAILY_LOSS_PCT=5.0
CA_MAX_DRAWDOWN_PCT=15.0

# Social sentiment (optional)
CA_TWITTER_BEARER_TOKEN=        # X API v2 (optional)
CA_TWITTER_SCRAPE_URL=          # Scraping proxy (optional)
CA_REDDIT_SUBREDDITS=["solana","cryptocurrency"]
```

### CLI Options

```bash
uv run python -m cryptoagent.cli.main SOL \
  --brain-model "openrouter/anthropic/claude-sonnet-4" \
  --research-model "openrouter/deepseek/deepseek-chat-v3-0324" \
  --macro-model "openrouter/deepseek/deepseek-chat-v3-0324" \
  --capital 50000 \
  --cycles 3 \
  --asset-type crypto \
  --exchange binance \
  -v  # verbose logging
```

## Project Structure

```
cryptoagent/
├── config.py                      # Pydantic settings (per-agent models, risk, social, etc.)
├── llm/
│   └── client.py                  # LiteLLM wrapper (call_llm, call_llm_json)
├── agents/
│   ├── research.py                # Market data + TA + on-chain analysis
│   ├── sentiment.py               # Reddit + Twitter + Fear & Greed + news sentiment
│   ├── macro.py                   # FRED macro data + regime analysis
│   ├── brain.py                   # Regime-aware reasoning + trade decisions
│   └── trader.py                  # Execution validation + routing
├── dataflows/
│   ├── aggregator.py              # Unified data interface (real providers + stub fallbacks)
│   ├── regime.py                  # Market regime classifier (bull/bear/sideways)
│   ├── market/
│   │   └── ccxt_provider.py       # OHLCV + 12 technical indicators via CCXT
│   ├── onchain/
│   │   ├── defillama.py           # DeFiLlama: TVL, DEX volume, fees
│   │   ├── solana_rpc.py          # Solana RPC: TPS, whale activity
│   │   └── fear_greed.py          # Alternative.me Fear & Greed Index
│   ├── social/
│   │   ├── reddit.py              # Reddit JSON API (no auth needed)
│   │   └── twitter.py             # X/Twitter (scraping proxy or official API v2)
│   ├── macro/
│   │   ├── fred.py                # FRED API: M2, Fed rate, Treasury yields
│   │   └── classifier.py          # Macro regime classifier (risk-on/risk-off)
│   └── news/
│       └── cryptopanic.py         # CryptoPanic RSS: crypto headlines
├── graph/
│   ├── state.py                   # AgentState TypedDict
│   └── builder.py                 # LangGraph wiring + TradingGraph (pre/post pipeline)
├── execution/
│   ├── paper_trade.py             # Paper trading simulator (fees, P&L)
│   └── router.py                  # Routes to paper/live backends
├── persistence/
│   ├── database.py                # SQLite connection manager + schema
│   ├── trade_logger.py            # Trade history CRUD
│   └── reflection_store.py        # Reflection memory CRUD
├── reflection/
│   └── manager.py                 # Level 1 (per-cycle) + Level 2 (cross-trial) reflections
├── risk/
│   └── sentinel.py                # Pre/post pipeline risk checks
└── cli/
    └── main.py                    # Typer CLI (--cycles for multi-cycle runs)
```

## Current Status

### Phase 1 (Complete)
- [x] 4-agent pipeline (Research → Sentiment → Brain → Trader)
- [x] Real market data via CCXT (SOL/USDT from Binance, 12 TA indicators)
- [x] LiteLLM integration (any provider, per-agent model config)
- [x] Paper trading with fee simulation
- [x] LangGraph parallel execution (Research + Sentiment)
- [x] CLI with full model override flags

### Phase 2 (Complete)
- [x] Real on-chain data (DeFiLlama TVL/DEX volume/fees, Solana RPC TPS/whale activity)
- [x] Real social sentiment (Reddit JSON API, X/Twitter dual-backend)
- [x] Fear & Greed Index (Alternative.me)
- [x] Market regime classifier (bull/bear/sideways with confidence score)
- [x] Two-level reflection memory (per-cycle + cross-trial strategic reviews)
- [x] SQLite persistence (trades + reflections)
- [x] Risk Sentinel (daily loss limit, drawdown cap, volatility spike detection)
- [x] Multi-cycle CLI (`--cycles N`) with portfolio carry-forward
- [x] Graceful degradation (real data → stub fallback on API failure)

### Phase 3 (Complete)
- [x] Real macro data via FRED API (M2 money supply, Fed Funds Rate, Treasury yields, yield curve)
- [x] Macro regime classifier (risk-on / risk-off / neutral heuristic)
- [x] CryptoPanic RSS news integration (crypto headlines into Sentiment agent)
- [x] 5th Macro Analyst agent (parallel with Research + Sentiment)
- [x] Brain agent macro context (both market + macro regimes)
- [x] Graceful degradation (real FRED data -> stub fallback without API key)

### Planned
- [ ] Equity support (Alpaca data provider + broker execution)
- [ ] Live trading execution
- [ ] Correlation engine (historical signal accuracy matrix)
- [ ] Web dashboard

## Requirements

- Python >= 3.13
- [uv](https://github.com/astral-sh/uv) for package management
- At least one LLM API key (OpenAI, Anthropic, DeepSeek, OpenRouter, or local Ollama)
