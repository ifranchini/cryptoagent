# CryptoAgent: Architecture

> Multi-agent LLM crypto trading system — paper trading, 5-agent pipeline, signal correlation
> Last updated: March 2026

For the long-term vision (debate, multi-strategy, backtesting, live execution), see [VISION.md](VISION.md).
For research background, see [crypto-trading-agents-research.md](crypto-trading-agents-research.md).

---

## Design Philosophy

**Core thesis:** Compete on *information edge* (better reasoning, better data fusion), NOT speed edge.

**Key principles:**
- **On-chain data as primary signal** — CryptoTrade ablation proved on-chain tx stats cause the biggest performance drop (-15.77%) when removed
- **Two-level reflection** — Per-cycle tactical + cross-trial strategic memory (proven +11.33% impact)
- **Fact-subjectivity aware reasoning** — FS-ReasoningAgent showed separating factual/subjective reasoning improves profits 7-10%. Weight facts more in bear markets, narrative more in bull markets
- **Risk gates before execution** — Pre-pipeline drawdown checks + post-pipeline position sizing guards
- **Paper trade first** — DeepFund (NeurIPS 2025) proved even top LLMs lose money in live trading

---

## System Overview

```
DATA LAYER (CCXT + DeFiLlama + Solana RPC + Reddit + X/Twitter + Fear & Greed + FRED + CryptoPanic + Snapshot + GitHub)
        │
  ┌─────┼─────┐
  ▼     ▼     ▼
Research Sentiment Macro  ← cheap/fast LLMs (parallel)
  │     │     │
  └─────┼─────┘
        ▼
      Brain                ← best reasoning LLM (+ regime, macro, on-chain, protocol, reflections)
        │
        ▼
      Trader               ← fast LLM → paper execution

Pre-pipeline:  Risk Sentinel pre-check, regime classification, reflection loading
Post-pipeline: Trade logging (SQLite), Level 1/2 reflection generation
```

The pipeline is orchestrated by LangGraph with fan-out (3 analysts run in parallel) and fan-in (Brain waits for all three before running).

---

## Agents

### Research Agent
**Model:** configurable (default: cheap/fast)
**Inputs:** market_data (OHLCV + 12 TA indicators), onchain_data (DeFiLlama TVL/fees, Solana RPC whale activity), protocol_data (governance, dev activity)
**Output:** `research_report` — comprehensive technical + on-chain + protocol analysis

### Sentiment Agent
**Model:** configurable (default: cheap/fast)
**Inputs:** Reddit sentiment, X/Twitter posts, Fear & Greed Index, news headlines (CryptoPanic)
**Output:** `sentiment_report` — market mood assessment with narrative themes

### Macro Agent
**Model:** configurable (default: cheap/fast)
**Inputs:** FRED data (M2 money supply, Fed Funds Rate, Treasury yields, yield curve), macro regime
**Output:** `macro_report` — macroeconomic environment assessment and crypto implications

### Brain Agent
**Model:** configurable (default: best reasoning model)
**Inputs:** All three analyst reports + market regime + cross-trial reflections + signal accuracy report
**Output:** `brain_decision` (JSON) — action (BUY/SELL/HOLD), asset, size_pct, stop_loss_pct, take_profit_pct, confidence (1-10), regime, rationale

The Brain system prompt includes:
- Regime confirmation/override guidance
- Fact/subjective signal weighting (70-80% facts in bear, 50-60% in bull)
- Signal accuracy weighting by timeframe (from correlation engine)
- Cross-trial memory incorporation

### Trader Agent
**Model:** configurable (default: fast)
**Inputs:** brain_decision, portfolio_state, market_data, risk_verdict
**Output:** `trade_result` — executes paper trade if risk allows, returns execution details

---

## Data Layer

### Implemented Data Sources

| Source | API | Data Provided | Status |
|--------|-----|--------------|--------|
| CCXT | Free | OHLCV, order book, tickers (SOL/USDT) | Real |
| DeFiLlama | Free | TVL, DEX volume, fees, revenue, protocol data | Real |
| Solana RPC | Free | TPS, whale activity estimates | Real |
| Reddit | Free | Post sentiment via JSON API | Real |
| X/Twitter | Bearer token or scraper | Influencer/community posts | Real (requires config) |
| Fear & Greed | Free (Alternative.me) | Index value (0-100) | Real |
| FRED | Free (API key) | M2, Fed Funds Rate, Treasury yields | Real |
| CryptoPanic | Free (RSS) | Crypto news headlines | Real |
| Snapshot | Free (GraphQL) | Governance proposals + voting | Real |
| GitHub | Free | Commit frequency, contributor health | Real |

All data providers degrade gracefully to stubs if APIs are unavailable.

### Technical Indicators (12)

RSI-14, MACD (line + signal + histogram), Bollinger Bands (upper/lower/mid), SMA-20, SMA-50, ATR-14, volume change

---

## State Schema

```python
class AgentState(TypedDict, total=False):
    # Target
    token: str
    asset_type: str              # "crypto" | "equity"
    timestamp: str

    # Agent outputs
    research_report: str
    sentiment_report: str
    macro_report: str
    brain_decision: str          # JSON string
    trade_result: str

    # Context
    portfolio_state: PortfolioState
    market_data: dict            # OHLCV + indicators
    onchain_data: dict           # TVL, DEX volume, whale activity
    news_data: dict              # CryptoPanic headlines
    protocol_data: dict          # TVL, fees, governance, dev activity

    # Regime
    market_regime: str           # "bull" | "bear" | "sideways"
    regime_confidence: int       # 1-10
    macro_regime: str            # "risk_on" | "risk_off" | "neutral"
    fear_greed_index: int        # 0-100

    # Risk + Reflection
    risk_verdict: str            # "proceed" | "halt" | "reduce"
    cross_trial_reflections: list[str]
    reflection_memory: list[str]
    signal_report: str           # Signal accuracy report for Brain
```

---

## Signal Correlation Engine

Extracts 17 structured signals from each pipeline run across 5 sources:

| Source | Signals |
|--------|---------|
| Technical | RSI-14, MACD histogram, price vs SMA20, price vs SMA50, Bollinger Band position |
| On-chain | TVL trend, whale activity, DEX volume change |
| Sentiment | Fear & Greed (contrarian), Reddit sentiment keywords |
| Macro | macro_regime, market_regime, regime_confidence |
| Brain | brain_action, brain_confidence, brain_size_pct, brain_regime |

Signals are persisted to SQLite with timestamps and price snapshots. The evaluator checks outcomes at three timeframes (4h, 24h, 7d) and records whether signal direction matched actual price movement.

A signal accuracy report is generated and injected into the Brain agent's context, enabling it to weight signals by their historical accuracy.

---

## Reflection System

### Level 1 — Per-Cycle (runs every cycle)
- Input: brain_decision + trade_result + regime
- LLM generates 2-3 sentence tactical reflection
- Falls back to auto-generated text if LLM fails
- Stored in SQLite

### Level 2 — Cross-Trial (runs every N cycles, default 5)
- Input: recent Level 1 reflections
- LLM generates strategic review identifying patterns and adjustments
- Sliding window of last 3 Level 2 reflections injected into Brain prompt
- Stored in SQLite

---

## Risk Management

### Risk Sentinel (pre/post pipeline)
No LLM calls — pure threshold checks.

**Pre-check (before pipeline):**
- Daily loss limit (default 5% of net_worth)
- Drawdown check (net_worth vs initial_capital, default 15%)
- Verdict: "proceed" or "halt" (forces HOLD)

**Post-check (after brain_decision):**
- ATR volatility spike detection (halves position if ATR > multiplier × 2.5% of price)
- Position concentration check (caps at 25% of net_worth for BUY)
- Verdict: "proceed", "reduce" (modified size_pct), or "halt"

---

## Execution

Paper trading only (current state). Simulates trade execution with:
- Fee model (configurable, default 0.1%)
- Portfolio tracking: cash + holdings + net_worth
- Trade history logging to SQLite
- Support for BUY and SELL actions with fractional sizing

---

## Project Structure

```
cryptoagent/
├── agents/                     # 5 LLM-powered agents
│   ├── research.py             # Research Agent (technical + on-chain + protocol)
│   ├── sentiment.py            # Sentiment Agent (social + news + F&G)
│   ├── macro.py                # Macro Agent (FRED data + regime)
│   ├── brain.py                # Brain Agent (synthesis + decision)
│   └── trader.py               # Trader Agent (execution routing)
├── cli/main.py                 # Typer CLI entry point
├── config.py                   # Pydantic settings (CA_ env prefix)
├── dataflows/                  # Data providers
│   ├── market/ccxt_provider.py # OHLCV + indicators via CCXT
│   ├── onchain/                # DeFiLlama, Solana RPC
│   ├── social/                 # Reddit, Twitter, Fear & Greed
│   ├── macro/fred_provider.py  # FRED API (M2, rates, yields)
│   ├── news/cryptopanic.py     # CryptoPanic RSS
│   ├── protocol/               # DeFiLlama protocol, Snapshot, GitHub
│   └── regime.py               # Market regime classifier
├── execution/
│   ├── paper_trade.py          # Paper trading engine
│   └── router.py               # Execution routing
├── graph/
│   ├── builder.py              # LangGraph wiring + pre/post pipeline
│   └── state.py                # AgentState TypedDict
├── llm/client.py               # LiteLLM wrapper (call_llm, call_llm_json)
├── persistence/
│   ├── database.py             # SQLite connection + schema (5 tables)
│   ├── trade_logger.py         # Trade CRUD
│   ├── reflection_store.py     # Reflection CRUD
│   └── signals.py              # Signal + price snapshot CRUD
├── reflection/manager.py       # Level 1 + Level 2 reflection generation
├── risk/sentinel.py            # Pre/post pipeline threshold checks
└── signals/
    ├── extractor.py            # Extract 17 signals from AgentState
    ├── evaluator.py            # Evaluate signal outcomes at 4h/24h/7d
    ├── logger.py               # Persist signals + price snapshots
    └── report.py               # Generate accuracy report for Brain
```

---

## Key Technical Decisions

| Decision | Choice | Why |
|----------|--------|-----|
| LLM routing | LiteLLM | Any provider, per-agent model config |
| Orchestration | LangGraph | Fan-out/fan-in, modular, extensible |
| Market data | CCXT | Free, 100+ exchanges, battle-tested |
| Persistence | SQLite | Zero-config, sufficient for single-process |
| Config | Pydantic Settings | Validated, env vars with CA_ prefix |
| CLI | Typer + Rich | Clean output, model override flags |
| Package manager | uv | Fast, deterministic, replaces pip/poetry |

### Decision Frequency
- Default: per CLI invocation or `--cycles N` for multi-cycle
- Multi-cycle carries forward portfolio state and reflections

### Cost per Cycle
~100K tokens total across all agents. With cheap models for analysts and Sonnet for Brain: ~$0.10-0.30 per cycle.
