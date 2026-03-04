# CryptoAgent

Multi-agent LLM trading system. 5 specialized agents collaborate to analyze markets and execute paper trades, each powered by a different LLM suited to its role.

## Architecture

```
DATA LAYER (CCXT + DeFiLlama + Solana RPC + Reddit + X/Twitter + Fear & Greed + FRED + CryptoPanic + Snapshot + GitHub)
        │
  ┌─────┼─────┐
  ▼     ▼     ▼
Research Sentiment Macro  ← cheap/fast LLMs (parallel)
  │     │     │
  └─────┼─────┘
        ▼
      Brain                ← best reasoning LLM (+ regime, on-chain, macro, protocol, reflections)
        │
        ▼
      Trader               ← fast LLM → paper/live execution
```

**Pre-pipeline:** Risk Sentinel pre-check, market regime classification, cross-trial reflection loading, signal evaluation.
**Post-pipeline:** Risk Sentinel post-check, trade logging (SQLite/PostgreSQL), Level 1/2 reflection generation, signal extraction.

| Agent | Role | Default Model |
|-------|------|---------------|
| **Research** | Market data + TA indicators + on-chain (DeFiLlama, Solana RPC) + protocol fundamentals | `deepseek/deepseek-chat-v3-0324` |
| **Sentiment** | Reddit posts, X/Twitter sentiment, Fear & Greed Index, crypto news | `deepseek/deepseek-chat-v3-0324` |
| **Macro** | FRED macro data (M2, Fed rate, yields, yield curve), macro regime | `deepseek/deepseek-chat-v3-0324` |
| **Brain** | Regime-aware signal weighting, cross-trial reflections, signal accuracy, trade decision | `anthropic/claude-sonnet-4` |
| **Trader** | Execution validation, order routing, paper trading | `deepseek/deepseek-chat-v3-0324` |

## Key Design Choices

- **Model-agnostic** — [LiteLLM](https://github.com/BerriAI/litellm) as unified gateway. Supports 100+ providers (OpenAI, Anthropic, DeepSeek, Ollama, OpenRouter, etc.). Each agent can use a different model.
- **LangGraph orchestration** — Research + Sentiment + Macro run in parallel, all three feed into Brain, then Trader executes. Clean 5-node DAG.
- **Real on-chain data** — DeFiLlama (TVL, DEX volume, fees) + Solana RPC (TPS, whale activity). Graceful degradation to stubs on API failure.
- **Protocol fundamentals** — DeFiLlama (per-protocol TVL, fees, revenue), Snapshot GraphQL (governance proposals), GitHub API (commit activity, health). All free, no auth required.
- **Real social sentiment** — Reddit JSON API (r/solana, r/cryptocurrency) + X/Twitter (scraping proxy or official API v2). Fear & Greed Index from Alternative.me.
- **Signal correlation engine** — Extracts 17 structured signals per cycle, tracks outcomes at 4h/24h/7d, generates accuracy reports injected into Brain context.
- **Two-level reflection memory** — Level 1 (per-cycle lessons) + Level 2 (cross-trial strategic reviews). Stored in SQLite, injected into Brain prompt.
- **Risk Sentinel** — Pre/post pipeline threshold checks (daily loss, drawdown, volatility spikes). Can halt trading or reduce position sizes.
- **Market regime detector** — Pure numeric heuristic (price vs SMA50, RSI, MACD histogram). Regime + confidence fed to Brain.
- **FS-ReasoningAgent pattern** — Research labels findings as `[FACT]` vs `[INFERENCE]`. Brain weights factual signals more heavily in bearish/uncertain regimes.

## Quick Start

### Pipeline (CLI)

```bash
# Install
uv sync

# Configure (need at least one LLM provider key)
cp .env.example .env
# Edit .env — set your API key(s) and model preferences

# Single cycle
uv run python -m cryptoagent.cli.main SOL

# Multi-cycle with portfolio carry-forward
uv run python -m cryptoagent.cli.main SOL --cycles 6

# Override models via CLI
uv run python -m cryptoagent.cli.main SOL \
  --brain-model "openrouter/anthropic/claude-sonnet-4" \
  --capital 50000 --cycles 3 -v
```

### Web Dashboard

```bash
cd dashboard
npm install
npm run dev             # http://localhost:3000
```

Requires a Neon PostgreSQL database. Set `DATABASE_URL` in `dashboard/.env.local`:

```bash
DATABASE_URL=postgresql://user:pass@host/db?sslmode=require
```

Push the schema, then seed data by running pipeline cycles with `CA_DATABASE_URL` set to the same connection string.

```bash
npm run db:push         # push Drizzle schema to Neon
```

### FastAPI Sidecar (run trigger from dashboard)

```bash
uvicorn api.server:app --reload   # http://localhost:8000
```

Set `SIDECAR_URL=http://localhost:8000` in `dashboard/.env.local` to enable the "Run Pipeline" button.

## Testing

```bash
# Python unit/integration tests (126 tests)
pytest -q

# Dashboard E2E tests (32 tests, requires dev server running)
cd dashboard && npx playwright test

# Dashboard E2E with visible browser
cd dashboard && npx playwright test --headed

# Dashboard E2E interactive UI
cd dashboard && npx playwright test --ui
```

Install Playwright browsers on first run: `cd dashboard && npx playwright install chromium`

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

# Persistence (SQLite default, PostgreSQL for dashboard sync)
CA_DB_PATH=data/cryptoagent.db
CA_DATABASE_URL=                      # set to Neon URL for dual-write

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

## Project Structure

```
cryptoagent/
├── config.py                      # Pydantic settings (per-agent models, risk, social, etc.)
├── llm/client.py                  # LiteLLM wrapper (call_llm, call_llm_json)
├── agents/                        # 5 LLM-powered agents
│   ├── research.py                # Market data + TA + on-chain + protocol analysis
│   ├── sentiment.py               # Reddit + Twitter + Fear & Greed + news sentiment
│   ├── macro.py                   # FRED macro data + regime analysis
│   ├── brain.py                   # Regime-aware reasoning + trade decisions
│   └── trader.py                  # Execution validation + routing
├── dataflows/                     # Data providers
│   ├── aggregator.py              # Unified data interface (real + stub fallbacks)
│   ├── regime.py                  # Market regime classifier (bull/bear/sideways)
│   ├── market/ccxt_provider.py    # OHLCV + 12 TA indicators via CCXT
│   ├── onchain/                   # DeFiLlama, Solana RPC, Fear & Greed
│   ├── social/                    # Reddit, Twitter
│   ├── macro/                     # FRED API, macro regime classifier
│   ├── news/cryptopanic.py        # CryptoPanic RSS headlines
│   └── protocol/                  # DeFiLlama protocol, Snapshot, GitHub
├── graph/
│   ├── state.py                   # AgentState TypedDict
│   └── builder.py                 # LangGraph wiring + TradingGraph
├── execution/
│   ├── paper_trade.py             # Paper trading simulator (fees, P&L)
│   └── router.py                  # Routes to paper/live backends
├── persistence/
│   ├── database.py                # SQLite/PostgreSQL connection + schema
│   ├── trade_logger.py            # Trade history CRUD
│   ├── reflection_store.py        # Reflection memory CRUD
│   └── signals.py                 # Signal + price snapshot CRUD
├── reflection/manager.py          # Level 1 + Level 2 reflections
├── risk/sentinel.py               # Pre/post pipeline risk checks
├── signals/
│   ├── extractor.py               # Extract 17 signals from AgentState
│   ├── evaluator.py               # Evaluate outcomes at 4h/24h/7d
│   ├── logger.py                  # Persist signals + price snapshots
│   └── report.py                  # Accuracy report for Brain
├── cli/main.py                    # Typer CLI entry point
└── tests/                         # 126 unit/integration tests

dashboard/                         # Next.js web dashboard
├── app/                           # Pages: overview, trades, signals, reflections, chat
├── components/                    # UI components (shadcn/ui + custom)
├── lib/                           # Drizzle schema, DB connection, types
├── e2e/                           # 32 Playwright E2E tests
└── api/                           # API routes (data, chat, run trigger)

api/server.py                      # FastAPI sidecar for pipeline execution
```

## Requirements

- Python >= 3.13
- [uv](https://github.com/astral-sh/uv) for package management
- Node.js >= 18 (for dashboard)
- At least one LLM API key (OpenAI, Anthropic, DeepSeek, OpenRouter, or local Ollama)
