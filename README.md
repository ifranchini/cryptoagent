# CryptoAgent

Multi-agent LLM trading system. 4 specialized agents collaborate to analyze markets and execute paper trades, each powered by a different LLM suited to its role.

## Architecture

```
DATA LAYER (CCXT + stubs)
        │
  ┌─────┴─────┐
  ▼           ▼
Research   Sentiment     ← cheap/fast LLMs (parallel)
  │           │
  └─────┬─────┘
        ▼
      Brain              ← best reasoning LLM
        │
        ▼
      Trader             ← fast LLM → paper/live execution
```

| Agent | Role | Default Model |
|-------|------|---------------|
| **Research** | Market data + TA indicators + on-chain + macro | `deepseek/deepseek-chat-v3-0324` |
| **Sentiment** | Social signals, news, Fear & Greed | `deepseek/deepseek-chat-v3-0324` |
| **Brain** | Regime detection, signal weighting, trade decision | `anthropic/claude-sonnet-4` |
| **Trader** | Execution validation, order routing, paper trading | `deepseek/deepseek-chat-v3-0324` |

## Key Design Choices

- **Model-agnostic** — [LiteLLM](https://github.com/BerriAI/litellm) as unified gateway. Supports 100+ providers (OpenAI, Anthropic, DeepSeek, Ollama, OpenRouter, etc.). Each agent can use a different model.
- **LangGraph orchestration** — Research + Sentiment run in parallel, both feed into Brain, then Trader executes. Clean 4-node DAG.
- **Multi-asset ready** — Shared reasoning layer for crypto and equities. Only data providers and execution backends differ per asset class.
- **FS-ReasoningAgent pattern** — Research labels findings as `[FACT]` vs `[INFERENCE]`. Brain weights factual signals more heavily in bearish/uncertain regimes.

## Quick Start

```bash
# Install
cd cryptoagent
uv sync

# Configure (need at least one LLM provider key)
cp .env.example .env
# Edit .env — set your API key(s) and model preferences

# Run
uv run python -m cryptoagent.cli.main SOL
```

## Configuration

All settings via environment variables (prefix `CA_`) or `.env` file:

```bash
# Per-agent models (any LiteLLM model string)
CA_RESEARCH_MODEL=openrouter/deepseek/deepseek-chat-v3-0324
CA_SENTIMENT_MODEL=openrouter/deepseek/deepseek-chat-v3-0324
CA_BRAIN_MODEL=openrouter/anthropic/claude-sonnet-4
CA_TRADER_MODEL=openrouter/deepseek/deepseek-chat-v3-0324

# Asset & execution
CA_TARGET_TOKEN=SOL
CA_EXCHANGE=binance
CA_EXECUTION_MODE=paper
CA_INITIAL_CAPITAL=10000.0
```

### CLI Options

```bash
uv run python -m cryptoagent.cli.main SOL \
  --brain-model "openrouter/anthropic/claude-sonnet-4" \
  --research-model "openrouter/deepseek/deepseek-chat-v3-0324" \
  --capital 50000 \
  --asset-type crypto \
  --exchange binance \
  -v  # verbose logging
```

## Project Structure

```
cryptoagent/
├── config.py                      # Pydantic settings (per-agent models, asset, execution)
├── llm/
│   └── client.py                  # LiteLLM wrapper (call_llm, call_llm_json)
├── agents/
│   ├── research.py                # Market data + TA analysis
│   ├── sentiment.py               # Social/news sentiment
│   ├── brain.py                   # Core reasoning + trade decisions
│   └── trader.py                  # Execution validation + routing
├── dataflows/
│   ├── aggregator.py              # Unified data interface
│   └── market/
│       └── ccxt_provider.py       # OHLCV + 12 technical indicators via CCXT
├── graph/
│   ├── state.py                   # AgentState TypedDict
│   └── builder.py                 # LangGraph wiring + TradingGraph class
├── execution/
│   ├── paper_trade.py             # Paper trading simulator (fees, P&L)
│   └── router.py                  # Routes to paper/live backends
└── cli/
    └── main.py                    # Typer CLI entry point
```

## Current Status (Phase 1)

- [x] 4-agent pipeline (Research → Sentiment → Brain → Trader)
- [x] Real market data via CCXT (SOL/USDT from Binance, 12 TA indicators)
- [x] LiteLLM integration (any provider, per-agent model config)
- [x] Paper trading with fee simulation
- [x] LangGraph parallel execution (Research + Sentiment)
- [x] CLI with full model override flags
- [ ] Real sentiment data (Twitter, Reddit, news APIs)
- [ ] Real on-chain data (TVL, whale flows, active addresses)
- [ ] Real macro data (DXY, Fed, S&P 500)
- [ ] Reflection memory (past decisions + outcomes fed back to Brain)
- [ ] Equity support (Alpaca data provider + broker execution)
- [ ] Live trading execution
- [ ] Correlation engine (historical signal accuracy matrix)

## Requirements

- Python >= 3.13
- [uv](https://github.com/astral-sh/uv) for package management
- At least one LLM API key (OpenAI, Anthropic, DeepSeek, OpenRouter, or local Ollama)
