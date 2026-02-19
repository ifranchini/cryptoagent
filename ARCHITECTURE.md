# CryptoAgent: Architecture Plan

> Multi-agent LLM crypto trading system built on TradingAgents + CryptoTrade patterns
> Enhanced with insights from HedgeAgents, FS-ReasoningAgent, ContestTrade, WebCryptoAgent, DeepFund, FINSABER, MEFAI, and MountainLion
> Last updated: February 18, 2026 (Exa research sweep integrated)

---

## Table of Contents

1. [Design Philosophy](#1-design-philosophy)
2. [High-Level Architecture](#2-high-level-architecture)
3. [What We Keep from TradingAgents](#3-what-we-keep-from-tradingagents)
4. [What We Adopt from CryptoTrade](#4-what-we-adopt-from-cryptotrade)
5. [What We Replace / Add](#5-what-we-replace--add)
6. [Agent Definitions](#6-agent-definitions)
7. [Data Layer](#7-data-layer)
8. [Execution Engine](#8-execution-engine)
9. [LangGraph Flow](#9-langgraph-flow)
10. [State Schema](#10-state-schema)
11. [Reflection & Memory System](#11-reflection--memory-system)
12. [Historical Signal Correlation Engine](#12-historical-signal-correlation-engine)
13. [Macro & Insider Intelligence Layer](#13-macro--insider-intelligence-layer)
14. [Multi-Strategy Parallel Execution](#14-multi-strategy-parallel-execution)
15. [Risk Profile Configurations](#15-risk-profile-configurations)
16. [Risk Management](#16-risk-management)
17. [Decoupled Risk Sentinel](#17-decoupled-risk-sentinel-from-webcryptoagent)
18. [Fact-Subjectivity Aware Reasoning](#18-fact-subjectivity-aware-reasoning-from-fs-reasoningagent)
19. [Competitive Agent Scoring](#19-competitive-agent-scoring-from-contesttrade)
20. [Hedging Layer](#20-hedging-layer-from-hedgeagents)
21. [Backtesting Harness](#21-backtesting-harness)
22. [Infrastructure & Deployment](#22-infrastructure--deployment)
23. [Project Structure](#23-project-structure)
24. [Implementation Phases](#24-implementation-phases)
25. [Key Technical Decisions](#25-key-technical-decisions)

---

## 1. Design Philosophy

**Core thesis:** Compete on *information edge* (better reasoning, better data fusion), NOT speed edge. We are not building an HFT bot or a memecoin sniper.

**Hybrid approach:** We combine the best of two academic frameworks:
- **TradingAgents** provides the *orchestration backbone*: LangGraph multi-agent pipeline, bull/bear debate, 3-perspective risk gate, modular LLM provider system
- **CryptoTrade** provides the *crypto intelligence patterns*: on-chain data integration (proven as the #1 signal in ablation studies), two-level reflection system, crypto-specific prompting, and a tested trading environment model

Neither framework alone is sufficient. TradingAgents has no crypto support. CryptoTrade has no debate mechanism, no risk management layer, and no execution engine. The hybrid gives us both.

**Principles:**
- **Multi-agent debate over single-agent decisions** -- Reduce hallucination and bias by forcing bull/bear arguments before every trade (from TradingAgents)
- **On-chain data as the primary signal** -- CryptoTrade's ablation study proved on-chain tx stats cause the biggest performance drop when removed (-15.77%). This is our #1 data priority
- **Two-level reflection** -- In-context reflection per cycle (adjust aggressiveness) + cross-trial memory (learn from failures). Proven by CryptoTrade to be the second most valuable component (-11.33% when removed)
- **On-chain + off-chain fusion** -- Unique to crypto, and poorly done by everyone else. Whale movements + social sentiment + technical analysis + protocol fundamentals
- **Adaptive risk management** -- Not just stop-losses. An agent that understands regime changes (bull/bear/sideways/crash) and adjusts position sizing dynamically (from TradingAgents, extended)
- **Fact-subjectivity aware reasoning** -- FS-ReasoningAgent (NUS, 2024) proved that separating factual and subjective reasoning improves profits by 7-10%. Subjective signals (narrative, hype) matter more in bull markets; factual signals (on-chain, fundamentals) matter more in bear markets. Our regime detector should dynamically adjust this weighting
- **Decoupled control architecture** -- WebCryptoAgent (Jan 2026) showed that strategic reasoning (hourly) must be decoupled from real-time risk monitoring (per-second). The trading pipeline takes minutes; crashes happen in seconds. A separate, lightweight risk sentinel runs independently
- **Competitive agent selection** -- ContestTrade (Aug 2025) proved that running multiple competing agents and selecting top performers via real-time scoring significantly outperforms single-agent approaches. We apply this to our analyst layer
- **Explainability first** -- Every trade decision produces a human-readable rationale with full audit trail. This is a moat AND a trust builder. VET framework (Dec 2025) provides formal verification of agent outputs
- **Paper trade first, real capital later** -- Built-in simulation mode as a first-class citizen, modeled on CryptoTrade's ETHTradingEnv pattern. DeepFund (NeurIPS 2025) proved that even top LLMs (DeepSeek-V3, Claude-3.7-Sonnet) lose money in live trading -- historical backtesting is inflated by "time travel" (using future knowledge from training data)

**Target market:** Mid-cap altcoins across multiple chains (Ethereum, Solana, Base, Arbitrum). NOT BTC/ETH HFT (too competitive), NOT memecoin sniping (too latency-dependent).

---

## 2. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        CRYPTOAGENT SYSTEM                          │
│                                                                     │
│  ┌──────────────────────── DATA LAYER ─────────────────────────┐   │
│  │                                                              │   │
│  │  ┌─────────┐ ┌──────────┐ ┌──────────┐ ┌───────────────┐   │   │
│  │  │ On-Chain │ │ Market   │ │ Social/  │ │  Protocol     │   │   │
│  │  │ Intel   │ │ Data     │ │ News     │ │  Fundamentals │   │   │
│  │  └────┬────┘ └────┬─────┘ └────┬─────┘ └──────┬────────┘   │   │
│  │       └───────────┼───────────┼───────────────┘             │   │
│  │                   ▼                                          │   │
│  │          ┌─────────────────┐                                 │   │
│  │          │  Data Aggregator │  (normalize, cache, stream)    │   │
│  │          └────────┬────────┘                                 │   │
│  └───────────────────┼──────────────────────────────────────────┘   │
│                      ▼                                              │
│  ┌──────────────── AGENT LAYER (LangGraph) ────────────────────┐   │
│  │                                                              │   │
│  │  Phase 1: ANALYSIS (concurrent)                              │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │   │
│  │  │ On-Chain │ │Technical │ │Sentiment │ │ Protocol │       │   │
│  │  │ Analyst  │ │ Analyst  │ │ Analyst  │ │ Analyst  │       │   │
│  │  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘       │   │
│  │       └─────────────┼───────────┼─────────────┘             │   │
│  │                     ▼                                        │   │
│  │  Phase 2: RESEARCH (debate)                                  │   │
│  │  ┌────────────┐   ◄──►   ┌────────────┐                     │   │
│  │  │   Bull     │  debate   │   Bear     │                     │   │
│  │  │ Researcher │  rounds   │ Researcher │                     │   │
│  │  └────────────┘           └────────────┘                     │   │
│  │         │                         │                          │   │
│  │         └─────────┬───────────────┘                          │   │
│  │                   ▼                                          │   │
│  │  Phase 3: DECISION                                           │   │
│  │  ┌──────────────────────┐                                    │   │
│  │  │   Trader Agent       │                                    │   │
│  │  │   (synthesize +      │                                    │   │
│  │  │    decide action)    │                                    │   │
│  │  └──────────┬───────────┘                                    │   │
│  │             ▼                                                │   │
│  │  Phase 4: RISK GATE                                          │   │
│  │  ┌────────┐ ┌─────────┐ ┌──────────────┐                    │   │
│  │  │Aggress.│ │Neutral  │ │Conservative  │                    │   │
│  │  │Risk    │ │Risk     │ │Risk          │                    │   │
│  │  └───┬────┘ └────┬────┘ └──────┬───────┘                    │   │
│  │      └───────────┼─────────────┘                             │   │
│  │                  ▼                                           │   │
│  │  ┌──────────────────────┐                                    │   │
│  │  │   Risk Judge         │  approve / modify / reject         │   │
│  │  └──────────┬───────────┘                                    │   │
│  └─────────────┼────────────────────────────────────────────────┘   │
│                ▼                                                    │
│  ┌──────────── EXECUTION LAYER ────────────────────────────────┐   │
│  │                                                              │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌──────────────────┐    │   │
│  │  │ CEX Router  │  │ DEX Router  │  │ Paper Trade Sim  │    │   │
│  │  │ (CCXT)      │  │ (web3/sol)  │  │ (default mode)   │    │   │
│  │  └─────────────┘  └─────────────┘  └──────────────────┘    │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                ▼                                                    │
│  ┌──────────── REFLECTION LAYER ───────────────────────────────┐   │
│  │                                                              │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐   │   │
│  │  │  Trade Log   │  │  Reflection  │  │  Agent Memory   │   │   │
│  │  │  + P&L       │  │  Agent       │  │  (Redis/SQLite) │   │   │
│  │  └──────────────┘  └──────────────┘  └─────────────────┘   │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3. What We Keep from TradingAgents

TradingAgents source structure for reference:

```
tradingagents/
├── agents/
│   ├── analysts/          # fundamentals, market, news, social_media
│   ├── managers/          # portfolio/research manager
│   ├── researchers/       # bull/bear researchers
│   ├── risk_mgmt/         # aggressive, neutral, conservative + judge
│   ├── trader/            # trading decision maker
│   └── utils/
├── dataflows/             # Alpha Vantage, yFinance integrations
├── graph/
│   ├── setup.py           # LangGraph graph construction
│   ├── trading_graph.py   # TradingAgentsGraph orchestrator
│   ├── conditional_logic.py
│   ├── propagation.py
│   ├── reflection.py
│   └── signal_processing.py
├── llm_clients/           # Multi-provider LLM factory
└── default_config.py
```

**KEEP as-is:**
- `graph/setup.py` -- LangGraph topology (analyst -> debate -> trader -> risk gate -> judge). This flow is excellent.
- `graph/conditional_logic.py` -- Dynamic routing (`should_continue_debate()`, `should_continue_risk_analysis()`)
- `graph/reflection.py` -- Memory update mechanism (bull_memory, bear_memory, trader_memory, risk_manager_memory)
- `llm_clients/` -- Multi-provider factory (OpenAI, Anthropic, Google, Ollama). Works perfectly.
- `agents/researchers/` -- Bull/bear debate pattern. Core value of the framework.
- `agents/risk_mgmt/` -- Three-perspective risk analysis (aggressive/neutral/conservative) + judge. Keep entirely.
- `agents/trader/` -- Trader synthesis logic. Extend but don't replace.
- `default_config.py` -- Config pattern. Extend with crypto-specific fields.

**KEEP the pattern, rewrite the internals:**
- `agents/analysts/` -- Keep the 4-analyst concurrent pattern, but replace all 4 with crypto-specific analysts
- `graph/trading_graph.py` -- Keep the `TradingAgentsGraph` orchestrator pattern, extend for crypto
- `graph/propagation.py` -- Keep state initialization, modify fields for crypto state
- `graph/signal_processing.py` -- Replace stock signal processing with crypto signal processing

---

## 4. What We Adopt from CryptoTrade

CryptoTrade source structure for reference:

```
CryptoTrade/
├── run_agent.py              # Trial orchestrator (manages runs, memory updates)
├── eth_trial.py              # Core pipeline: analyst calls → trader → environment step
├── eth_env.py                # Trading environment (portfolio, execution, P&L)
├── env_history.py            # Prompt construction for all 4 agents + state tracking
├── generate_reflections.py   # Cross-trial reflection memory generation
├── utils.py                  # OpenAI API client with retry logic
├── run_baseline.py           # Baseline strategy comparison
└── data/                     # Historical price, on-chain, and news data
```

### What We Adopt (Patterns & Logic)

**1. On-Chain Analyst Prompt Pattern** (from `env_history.py`)

CryptoTrade proved that on-chain transaction statistics are the single most valuable signal (-15.77% when removed). We adopt their data schema and extend it:

```
CryptoTrade uses:                    We extend with:
├── Open price                       ├── (keep)
├── Daily transaction count          ├── (keep) + per-DEX breakdown
├── Active wallet numbers            ├── (keep) + whale wallet subset
├── Total value transferred          ├── (keep) + exchange inflow/outflow direction
├── Average gas price                ├── (keep) + fee revenue trends
├── Total gas consumed               ├── (keep)
├── SMA, MACD, Bollinger Bands       ├── (keep) + RSI, funding rates, open interest
│                                    ├── NEW: Whale wallet movements (top 100 holders)
│                                    ├── NEW: CEX deposit/withdrawal flows
│                                    ├── NEW: DEX liquidity depth changes
│                                    └── NEW: Smart money wallet tracking
```

**2. Two-Level Reflection System** (from `env_history.py` + `generate_reflections.py`)

CryptoTrade's reflection was proven as the second most valuable component. We adopt BOTH levels:

**Level 1 -- In-Context Reflection (per decision cycle):**
Adopted from CryptoTrade's reflection analyst prompt. The reflection agent reviews recent reasoning, actions, and daily returns, then provides strategic guidance:
- "Identify what information is currently more important"
- "Assess whether a more aggressive or conservative trading approach is warranted"
- This output is injected into the trader's prompt every cycle

**Level 2 -- Cross-Trial Memory (periodic):**
Adopted from CryptoTrade's `generate_reflections.py`. After unsuccessful periods, the system generates strategic reflections:
- "Think about the strategy and path you took... Devise a concise, new plan of action that accounts for your mistake"
- Maximum 3 historical reflections retained (sliding window -- same as CryptoTrade)
- Prepended to future decision contexts as few-shot learning

**Our extension:** We split Level 1 across all agent roles (TradingAgents pattern: bull_memory, bear_memory, trader_memory, risk_memory) rather than CryptoTrade's single-agent reflection. Each agent reflects on its own accuracy.

**3. Trading Environment Model** (from `eth_env.py`)

We adopt CryptoTrade's portfolio simulation pattern for our paper trading mode:

```python
# CryptoTrade's model (we adopt and extend):
Initial portfolio:  50% cash / 50% crypto (configurable in our version)
Action space:       [-1, +1] continuous (we extend to structured orders)
Fee model:          Gas + exchange fee per trade (we add slippage model)
P&L calculation:    ROI = (current_net_worth / starting_net_worth) - 1
Position tracking:  cash + (holdings × current_price)
```

**Our extensions beyond CryptoTrade's environment:**
- Multiple simultaneous positions (CryptoTrade: single asset only)
- Stop-loss / take-profit order types (CryptoTrade: market orders only)
- Cross-asset portfolio tracking
- Realistic slippage model based on order book depth

**4. Prompt Engineering Patterns** (from `env_history.py`)

CryptoTrade's prompt structure is proven effective. We adopt the core patterns:

```
Pattern 1: Chronological data window
  CryptoTrade feeds analysts a sliding window of N days of data in chronological order.
  We adopt this: each analyst receives a time-windowed, chronologically ordered data dump.

Pattern 2: Concise analyst output
  CryptoTrade instructs: "Write one concise paragraph to analyze..."
  We adopt this: analysts output structured, brief reports (not verbose reasoning).

Pattern 3: Synthesized trader prompt
  CryptoTrade injects all analyst reports into a single trader prompt with clear labels:
    "ON-CHAIN ANALYST REPORT: {report1}"
    "NEWS ANALYST REPORT: {report2}"
    "REFLECTION ANALYST REPORT: {report3}"
  We adopt this template pattern, extended with our 4 analysts + debate summary.

Pattern 4: Action as confidence signal
  CryptoTrade uses [-1, +1] where magnitude = confidence in direction.
  We adopt this concept: the trader's position size reflects conviction level.
```

**5. Ablation-Informed Data Priority**

CryptoTrade's ablation study gives us empirical guidance for data priority:

```
Priority 1 (MUST HAVE):  On-chain transaction statistics  → -15.77% impact when removed
Priority 2 (MUST HAVE):  Reflection/memory system         → -11.33% impact when removed
Priority 3 (HIGH VALUE): Technical indicators              → -11.20% impact when removed
Priority 4 (HIGH VALUE): News/sentiment                   → -8.78% impact when removed
Priority 5 (BASELINE):   Price data alone                 → Only 8.40% return (vs 28.47% full)
```

This means: **build the on-chain data pipeline BEFORE the news sentiment pipeline.** Most projects do the opposite.

### What We Do NOT Adopt from CryptoTrade

| CryptoTrade Feature | Why We Skip It |
|---------------------|----------------|
| Sequential pipeline (analyst → analyst → trader) | We use TradingAgents' concurrent fan-out + debate pattern instead |
| Single-asset only | We need multi-asset portfolio management |
| Daily-only frequency | We target 4-hour cycles (configurable) |
| OpenAI-only LLM | We use TradingAgents' multi-provider factory |
| No risk management layer | We use TradingAgents' 3-perspective risk gate |
| CC BY-NC-SA license code | We reference patterns/logic but reimplement in our Apache-2.0 codebase |
| Regex action parsing | Fragile; we use structured output (JSON) for trade decisions |
| No execution layer | We build our own (CCXT + DEX) |

---

## 5. What We Replace / Add

### Replace

| TradingAgents Component | Replace With | Why |
|------------------------|--------------|-----|
| `dataflows/alpha_vantage*.py` | Crypto data providers | No crypto support |
| `dataflows/y_finance*.py` | Crypto market data feeds | yFinance has limited crypto data |
| `agents/analysts/fundamentals_analyst.py` | `protocol_analyst.py` | Crypto doesn't have balance sheets -- it has TVL, token economics, governance |
| `agents/analysts/market_analyst.py` | `technical_analyst.py` | Same concept, crypto-specific indicators |
| `agents/analysts/news_analyst.py` | `sentiment_analyst.py` | Broader: X/Twitter, Telegram, Discord, not just news |
| `agents/analysts/social_media_analyst.py` | `onchain_analyst.py` | Replace generic social with on-chain intelligence |

### Add New

| New Component | Purpose |
|--------------|---------|
| `execution/` | CEX (CCXT) + DEX (web3/solana-py) trade execution |
| `execution/paper_trade.py` | Simulation mode (default) |
| `dataflows/onchain/` | Whale tracking, DEX flows, token transfers |
| `dataflows/market/` | CCXT OHLCV, order books, funding rates |
| `dataflows/social/` | X API, Telegram scraper, Discord webhooks |
| `dataflows/protocol/` | DeFiLlama, token unlocks, governance |
| `dataflows/streaming.py` | WebSocket real-time data ingestion |
| `backtesting/` | Historical replay engine for LLM agents |
| `agents/analysts/onchain_analyst.py` | Whale movements, smart money, DEX flows |
| `agents/analysts/protocol_analyst.py` | TVL, tokenomics, unlock schedules, governance |
| `graph/regime_detector.py` | Market regime classification (bull/bear/sideways/crash) |
| `notifications/` | Telegram/Discord alerts with trade rationale |

---

## 6. Agent Definitions

### Phase 1: Analysts (Concurrent, use `quick_think_llm`)

#### On-Chain Analyst
```
Role: Analyze blockchain-level data to detect smart money movements and network health
      THE #1 PRIORITY SIGNAL per CryptoTrade ablation study (-15.77% when removed)

Inputs (CryptoTrade proven baseline):
  - Daily transaction count
  - Active wallet numbers
  - Total value transferred
  - Average gas price
  - Total gas consumed

Inputs (our extensions):
  - Whale wallet movements (top 100 holders for target token)
  - DEX buy/sell volume and liquidity changes
  - Token transfer patterns (exchange inflows/outflows)
  - New contract deployments interacting with the token

Prompt pattern (adapted from CryptoTrade's env_history.py):
  "You are a {TOKEN} cryptocurrency on-chain analyst. The recent on-chain
   data is given in chronological order below: [windowed data]...
   Write one concise paragraph analyzing the on-chain signals and
   estimate their implications for price direction."

Output: On-chain signal report with confidence score
  - Whale accumulation/distribution status
  - Exchange flow direction (bullish/bearish)
  - Network health assessment
  - Notable on-chain events

Tools: get_whale_movements, get_dex_volume, get_exchange_flows, get_network_stats
```

#### Technical Analyst
```
Role: Apply quantitative technical analysis to price and volume data

Inputs:
  - OHLCV data (multiple timeframes: 1h, 4h, 1d)
  - Order book depth (top CEX)
  - Funding rates (perpetuals)
  - Open interest changes
  - Liquidation levels

Output: Technical signal report with confidence score
  - Trend direction and strength
  - Key support/resistance levels
  - Momentum indicators (RSI, MACD, Bollinger)
  - Volume profile analysis
  - Funding rate signal (overleveraged long/short)

Tools: get_ohlcv, get_order_book, get_funding_rates, get_open_interest, compute_indicators
```

#### Sentiment Analyst
```
Role: Gauge market sentiment from social and news sources

Inputs:
  - X/Twitter posts from key influencers and CT
  - Reddit mentions (r/cryptocurrency, token-specific subs)
  - News articles (crypto-native + mainstream)
  - Telegram/Discord group activity spikes
  - Fear & Greed Index

Output: Sentiment report with confidence score
  - Overall sentiment direction and intensity
  - Key narrative themes
  - Influencer consensus vs retail divergence
  - News catalyst identification
  - Sentiment momentum (improving/deteriorating)

Tools: get_twitter_sentiment, get_reddit_mentions, get_news_articles, get_fear_greed_index
```

#### Protocol Analyst
```
Role: Evaluate the fundamental health and trajectory of the crypto project

Inputs:
  - Total Value Locked (TVL) trend
  - Revenue and fee generation
  - Token unlock schedule (upcoming dilution)
  - Governance proposals (upcoming votes)
  - Developer activity (GitHub commits, releases)
  - Competitive positioning vs similar protocols
  - Audit status and security history

Output: Fundamental report with confidence score
  - Protocol health assessment
  - Tokenomics risk (upcoming unlocks, inflation)
  - Competitive moat evaluation
  - Catalyst calendar (upcoming events, launches)

Tools: get_tvl_data, get_token_unlocks, get_governance_activity, get_dev_activity
```

### Phase 2: Researchers (Debate, use `deep_think_llm`)

#### Bull Researcher
```
Role: Build the strongest possible case for entering/holding a position

Inputs: All 4 analyst reports
Memory: bull_memory (persistent across sessions, records past bull arguments + outcomes)

Process:
  1. Synthesize bullish signals across all reports
  2. Identify strongest catalysts and confluence zones
  3. Propose entry strategy and profit targets
  4. Counter anticipated bear arguments

Output: Bull thesis with conviction score (1-10)
```

#### Bear Researcher
```
Role: Build the strongest possible case against entering/for exiting a position

Inputs: All 4 analyst reports + Bull thesis
Memory: bear_memory (persistent, records past bear arguments + outcomes)

Process:
  1. Synthesize bearish signals and risks
  2. Identify potential black swans and downside scenarios
  3. Counter the bull thesis point by point
  4. Propose risk levels and stop-loss reasoning

Output: Bear thesis with conviction score (1-10)
```

**Debate rounds:** Configurable (default: 2). Bull and Bear respond to each other's arguments until `max_debate_rounds` reached or Research Manager intervenes.

### Phase 3: Trader Agent (use `deep_think_llm`)

```
Role: Synthesize all analysis into a concrete trading decision

Prompt pattern (adapted from CryptoTrade's template_s, extended):
  "You are an experienced cryptocurrency trader maximizing overall profit.
   You are assisted by analysts and researchers below.

   ON-CHAIN ANALYST REPORT:
   {onchain_report}

   TECHNICAL ANALYST REPORT:
   {technical_report}

   SENTIMENT ANALYST REPORT:
   {sentiment_report}

   PROTOCOL ANALYST REPORT:
   {protocol_report}

   BULL/BEAR DEBATE SUMMARY:      ← NEW (from TradingAgents, not in CryptoTrade)
   {debate_summary}

   REFLECTION ANALYST REPORT:     ← FROM CryptoTrade (proven +11.33% impact)
   {reflection_report}

   CURRENT PORTFOLIO STATE:
   {portfolio_state}

   MARKET REGIME: {regime}

   Based on the synthesized reports and debate, conclude a clear market
   view. Output your decision as structured JSON."

Inputs:
  - All 4 analyst reports
  - Bull/bear debate transcript and final theses (from TradingAgents)
  - Reflection analyst output (from CryptoTrade)
  - Current portfolio state (positions, cash, unrealized P&L)
  - Current market regime (from regime detector)

Memory: trader_memory (records past decisions + realized outcomes)

Output (structured JSON, not free-text float like CryptoTrade):
  - Action: BUY / SELL / HOLD / REDUCE
  - Asset and chain
  - Size: percentage of portfolio to allocate
  - Entry price range (limit order) or MARKET
  - Stop loss level
  - Take profit targets (multiple levels)
  - Time horizon: short (hours), medium (days), long (weeks)
  - Confidence: 1-10
  - Rationale: 3-5 sentence human-readable explanation
```

### Phase 4: Risk Gate (use `quick_think_llm`)

Same as TradingAgents: three perspectives (aggressive/neutral/conservative) debate, then Risk Judge makes final call:
- **APPROVE** -- execute as proposed
- **MODIFY** -- execute with adjusted size/stops
- **REJECT** -- do not execute, with reason

Additional crypto-specific risk checks:
- Portfolio concentration limits (no >25% in single asset)
- Correlation risk (avoid over-exposure to same sector)
- Liquidity check (can we exit this position without >2% slippage?)
- Smart contract risk flag (is the protocol audited? any recent exploits?)
- Market regime override (reduce all position sizes in crash regime)

---

## 7. Data Layer

### Architecture

```
dataflows/
├── __init__.py
├── config.py                  # API keys, rate limits, cache TTLs
├── aggregator.py              # Unified data interface for agents
├── cache.py                   # Redis/SQLite cache layer
├── streaming.py               # WebSocket manager for real-time feeds
│
├── market/                    # Price & trading data
│   ├── ccxt_provider.py       # CCXT: OHLCV, order books, tickers (CEX)
│   ├── funding_rates.py       # Perp funding rates (Binance, Bybit)
│   ├── liquidations.py        # Liquidation data (Coinglass API)
│   └── dex_prices.py          # DEX price feeds (DeFiLlama, Birdeye)
│
├── onchain/                   # Blockchain data
│   ├── whale_tracker.py       # Large holder movements (Arkham, Nansen-style)
│   ├── exchange_flows.py      # CEX inflow/outflow (CryptoQuant API or custom)
│   ├── dex_volume.py          # DEX trading volume by token (Dune queries)
│   ├── network_stats.py       # Active addresses, tx count (RPC or Dune)
│   └── token_transfers.py     # Significant transfers (custom RPC monitoring)
│
├── social/                    # Sentiment data
│   ├── twitter_sentiment.py   # X API v2: influencer posts, mention volume
│   ├── reddit_monitor.py      # Reddit API: mention frequency, sentiment
│   ├── news_aggregator.py     # Gnews/CryptoPanic: headline sentiment
│   └── fear_greed.py          # Alternative.me Fear & Greed Index
│
├── protocol/                  # Fundamental data
│   ├── defillama.py           # TVL, fees, revenue (DeFiLlama API)
│   ├── token_unlocks.py       # Vesting schedules (TokenUnlocks API)
│   ├── governance.py          # Snapshot/Tally: active proposals
│   └── dev_activity.py        # GitHub: commit frequency, contributors
│
├── macro/                     # NEW: Macroeconomic signals
│   ├── m2_money_supply.py     # Global M2 (FRED API for Fed, ECB/PBoC/BoJ feeds)
│   ├── dxy_index.py           # US Dollar Index (FRED API)
│   ├── fed_rates.py           # Fed funds rate + CME FedWatch expectations
│   ├── treasury_yields.py     # 2Y/10Y yields, yield curve (FRED API)
│   ├── global_liquidity.py    # Combined cross-central-bank liquidity index
│   └── macro_regime.py        # Classify: risk-on / risk-off / transition
│
└── insider/                   # NEW: Smart money / insider signals
    ├── congress_trades.py     # US Congress trades (Quiver Quantitative API)
    ├── whale_wallets.py       # Named whale tracking (Arkham Intelligence API)
    ├── vc_movements.py        # VC fund wallet activity (Arkham + Nansen)
    ├── exchange_insider.py    # Exchange reserve changes (CryptoQuant)
    └── token_insider.py       # Team/founder wallet movements
```

### Data Aggregator Interface

Every agent interacts with data through a single `DataAggregator` class:

```python
class DataAggregator:
    """Unified data interface for all agents.

    Each method returns a standardized dict that can be
    directly injected into an agent's LLM prompt.
    """

    def get_onchain_report(self, token: str, chain: str, lookback_days: int = 7) -> dict:
        """Whale movements, exchange flows, network stats, DEX volume."""

    def get_technical_report(self, token: str, timeframes: list[str] = ["1h", "4h", "1d"]) -> dict:
        """OHLCV, indicators, funding rates, open interest, order book."""

    def get_sentiment_report(self, token: str, lookback_hours: int = 48) -> dict:
        """Twitter, Reddit, news, Fear & Greed."""

    def get_protocol_report(self, token: str) -> dict:
        """TVL, revenue, unlocks, governance, dev activity."""

    def get_macro_report(self) -> dict:
        """M2 trend, DXY direction, Fed rate expectations, global liquidity, risk regime."""

    def get_insider_report(self, token: str, lookback_days: int = 30) -> dict:
        """Whale wallets, congress trades, VC movements, team wallet activity."""

    def get_signal_correlation_report(self, token: str, timeframe: str) -> dict:
        """Historical signal accuracy matrix at specified timeframe. From correlation engine."""

    def get_market_regime(self) -> str:
        """Current regime: 'bull' | 'bear' | 'sideways' | 'crash' | 'euphoria'."""

    def get_portfolio_state(self) -> dict:
        """Current positions, cash, unrealized P&L, exposure by chain."""
```

### Caching Strategy

| Data Type | Cache TTL | Storage |
|-----------|-----------|---------|
| OHLCV (1h+) | 5 minutes | Redis |
| Order book | 30 seconds | In-memory |
| On-chain metrics | 15 minutes | Redis |
| Whale movements | 5 minutes | Redis |
| Social sentiment | 10 minutes | Redis |
| Protocol fundamentals | 1 hour | Redis |
| News articles | 30 minutes | Redis |
| Historical (backtest) | Permanent | SQLite/Parquet |

---

## 8. Execution Engine

```
execution/
├── __init__.py
├── router.py              # Routes orders to correct venue
├── paper_trade.py         # Simulated execution (DEFAULT MODE)
├── cex_executor.py        # CCXT-based CEX execution
├── dex_executor.py        # On-chain DEX execution
├── order_manager.py       # Track open orders, fills, cancellations
├── position_tracker.py    # Track positions across all venues
└── slippage_model.py      # Estimate slippage before execution
```

### Execution Router Logic

```python
class ExecutionRouter:
    def execute(self, order: TradeOrder) -> ExecutionResult:
        # 1. Pre-flight checks
        self.check_sufficient_balance(order)
        self.check_liquidity(order)  # reject if slippage > 2%
        self.check_rate_limits()

        # 2. Route to venue
        if self.mode == "paper":
            return self.paper_executor.execute(order)

        if order.venue == "cex":
            return self.cex_executor.execute(order)  # via CCXT

        if order.venue == "dex":
            return self.dex_executor.execute(order)  # via web3/solana

        # 3. Post-execution
        self.position_tracker.update(result)
        self.trade_log.record(order, result)
        self.notify(result)  # Telegram/Discord alert
```

### Paper Trading (Default Mode)

Modeled on CryptoTrade's `ETHTradingEnv` pattern (50/50 cash/crypto split, fee model, ROI tracking) but significantly extended:

- **Portfolio model from CryptoTrade:** `net_worth = cash + (holdings x current_price)`, `ROI = (current_net_worth / starting_net_worth) - 1`
- **Extension:** Multiple simultaneous positions across assets (CryptoTrade: single asset)
- **Extension:** Realistic slippage model based on order book depth (CryptoTrade: fixed fees only)
- **Extension:** Stop-loss and take-profit order types (CryptoTrade: market orders only)
- Tracks virtual portfolio with real-time mark-to-market
- Produces identical trade logs and P&L reports as live trading
- Minimum 30 days paper trading before live deployment recommended

### CEX Execution (via CCXT)

Supported exchanges (initial):
- **Binance** -- Largest liquidity for most altcoins
- **Bybit** -- Best for perpetuals/funding rate strategies
- **OKX** -- Alternative liquidity venue

Order types: MARKET, LIMIT, STOP_LOSS, TAKE_PROFIT, trailing stop

### DEX Execution

- **Ethereum/L2s** -- via ethers.py + 1inch/Uniswap router
- **Solana** -- via solana-py + Jupiter aggregator
- Anti-MEV: use private RPCs (Flashbots Protect on ETH, Jito bundles on Solana)

---

## 9. LangGraph Flow

### Graph Topology

Extending TradingAgents' `setup.py` pattern:

```python
def setup_graph(self) -> StateGraph:
    graph = StateGraph(CryptoAgentState)

    # ── Phase 1: Analysts (concurrent via fan-out) ──
    graph.add_node("onchain_analyst", self.onchain_analyst_node)
    graph.add_node("onchain_tools", self.onchain_tool_node)

    graph.add_node("technical_analyst", self.technical_analyst_node)
    graph.add_node("technical_tools", self.technical_tool_node)

    graph.add_node("sentiment_analyst", self.sentiment_analyst_node)
    graph.add_node("sentiment_tools", self.sentiment_tool_node)

    graph.add_node("protocol_analyst", self.protocol_analyst_node)
    graph.add_node("protocol_tools", self.protocol_tool_node)

    # ── Phase 1.5: Regime Detection + In-Context Reflection ──
    graph.add_node("regime_detector", self.regime_detector_node)
    graph.add_node("reflection_analyst", self.reflection_analyst_node)  # FROM CryptoTrade

    # ── Phase 2: Research Debate ──
    graph.add_node("bull_researcher", self.bull_researcher_node)
    graph.add_node("bear_researcher", self.bear_researcher_node)
    graph.add_node("research_manager", self.research_manager_node)

    # ── Phase 3: Trading Decision ──
    graph.add_node("trader", self.trader_node)

    # ── Phase 4: Risk Gate ──
    graph.add_node("aggressive_risk", self.aggressive_risk_node)
    graph.add_node("neutral_risk", self.neutral_risk_node)
    graph.add_node("conservative_risk", self.conservative_risk_node)
    graph.add_node("risk_judge", self.risk_judge_node)

    # ── Phase 5: Execution (NEW) ──
    graph.add_node("executor", self.executor_node)

    # ── Phase 6: Post-Execution Reflection (CryptoTrade Level 2 + TradingAgents memory) ──
    graph.add_node("post_execution_reflection", self.post_execution_reflection_node)

    # ── EDGES ──

    # START -> All 4 analysts run concurrently (fan-out)
    graph.add_edge(START, "onchain_analyst")
    graph.add_edge(START, "technical_analyst")
    graph.add_edge(START, "sentiment_analyst")
    graph.add_edge(START, "protocol_analyst")

    # Each analyst has tool-calling loop
    # (same pattern as TradingAgents: analyst <-> tools conditional)
    graph.add_conditional_edges("onchain_analyst", self.should_continue_onchain,
        {"tools": "onchain_tools", "done": "regime_detector"})
    graph.add_edge("onchain_tools", "onchain_analyst")
    # ... (same pattern for technical, sentiment, protocol)

    # All analysts converge at regime_detector AND reflection_analyst (parallel)
    # Both run concurrently, then converge before debate
    graph.add_edge("regime_detector", "bull_researcher")
    graph.add_edge("regime_detector", "bear_researcher")
    graph.add_edge("reflection_analyst", "bull_researcher")  # reflection informs debate

    # Debate loop
    graph.add_conditional_edges("bull_researcher", self.should_continue_debate,
        {"continue": "bear_researcher", "done": "research_manager"})
    graph.add_conditional_edges("bear_researcher", self.should_continue_debate,
        {"continue": "bull_researcher", "done": "research_manager"})

    # Research -> Trader -> Risk Gate
    graph.add_edge("research_manager", "trader")
    graph.add_edge("trader", "aggressive_risk")

    # Risk debate loop (same as TradingAgents)
    graph.add_conditional_edges("aggressive_risk", self.should_continue_risk,
        {"continue": "neutral_risk", "done": "risk_judge"})
    graph.add_conditional_edges("neutral_risk", self.should_continue_risk,
        {"continue": "conservative_risk", "done": "risk_judge"})
    graph.add_conditional_edges("conservative_risk", self.should_continue_risk,
        {"continue": "aggressive_risk", "done": "risk_judge"})

    # Risk Judge -> Execute or End
    graph.add_conditional_edges("risk_judge", self.should_execute,
        {"execute": "executor", "reject": END})

    # Execute -> Post-Execution Reflection -> End
    graph.add_edge("executor", "post_execution_reflection")
    graph.add_edge("post_execution_reflection", END)

    return graph.compile()
```

### Key Differences from TradingAgents Graph

1. **Fan-out start** -- All 4 analysts run truly concurrently (TradingAgents chains them sequentially)
2. **Regime detector** node added between analysts and researchers -- classifies market state before debate
3. **Reflection analyst node** (from CryptoTrade) -- Runs in parallel with regime detector after analysts complete. Generates in-context reflection from recent performance history. Output feeds into the trader prompt alongside analyst reports and debate summary
4. **Executor node** -- TradingAgents ends at Risk Judge. We continue to actual execution
5. **Post-execution reflection node** -- After execution, updates agent memories and generates cross-trial reflections if performance thresholds are breached
6. **Convergence barrier** -- Regime detector acts as a sync point, waiting for all analysts + reflection analyst

### How Both Frameworks Map to Our Graph

```
CryptoTrade Pipeline:              Our LangGraph:
─────────────────────              ─────────────────
On-Chain Analyst ─────────►        On-Chain Analyst  ──┐
                                   Technical Analyst ──┤ (concurrent,
News Analyst ─────────────►        Sentiment Analyst ──┤  fan-out)
                                   Protocol Analyst  ──┘
                                          │
Reflection Analyst ───────►        Regime Detector + Reflection Analyst  (parallel)
                                          │
                                   Bull Researcher ◄──► Bear Researcher  (debate, from
                                          │              TradingAgents)
                                   Research Manager
                                          │
Trader Agent ─────────────►        Trader Agent (receives ALL of the above)
                                          │
(none) ───────────────────►        Risk Gate: Aggressive/Neutral/Conservative + Judge
                                          │              (from TradingAgents)
(none) ───────────────────►        Executor (CEX/DEX/Paper)
                                          │
(memory update) ──────────►        Post-Execution Reflection + Memory Update
```

---

## 10. State Schema

```python
from typing import TypedDict, Literal
from langgraph.graph import MessagesState

class CryptoAgentState(TypedDict):
    # ── Target ──
    token: str                          # e.g., "ARB", "SOL", "AAVE"
    chain: str                          # e.g., "ethereum", "solana", "arbitrum"
    timestamp: str                      # ISO 8601 decision timestamp

    # ── Analyst Reports ──
    onchain_report: str                 # On-chain analyst output
    technical_report: str               # Technical analyst output
    sentiment_report: str               # Sentiment analyst output
    protocol_report: str                # Protocol analyst output

    # ── Fact-Subjectivity Separation (from FS-ReasoningAgent) ──
    fact_weight: float                  # Regime-dependent: 0.4 (bull) to 0.8 (crash)
    subjective_weight: float            # Regime-dependent: 0.6 (bull) to 0.2 (crash)

    # ── Regime ──
    market_regime: Literal["bull", "bear", "sideways", "crash", "euphoria"]
    regime_confidence: float            # 0.0 - 1.0

    # ── Research ──
    bull_thesis: str
    bear_thesis: str
    bull_conviction: int                # 1-10
    bear_conviction: int                # 1-10
    debate_transcript: list[str]
    debate_round: int
    research_summary: str

    # ── Trading Decision ──
    trade_action: Literal["BUY", "SELL", "HOLD", "REDUCE"]
    trade_size: float                   # % of portfolio
    trade_entry_price: float | None     # None = market order
    trade_stop_loss: float
    trade_take_profit: list[float]      # Multiple TP levels
    trade_timeframe: Literal["short", "medium", "long"]
    trade_confidence: int               # 1-10
    trade_rationale: str                # Human-readable explanation

    # ── Risk Assessment ──
    risk_aggressive_view: str
    risk_neutral_view: str
    risk_conservative_view: str
    risk_discuss_round: int
    risk_decision: Literal["APPROVE", "MODIFY", "REJECT"]
    risk_modifications: str | None      # If MODIFY: what changed

    # ── Reflection (from CryptoTrade, Level 1: in-context) ──
    reflection_report: str              # In-context reflection analyst output
    reflection_window: list[dict]       # Last N decisions: {reasoning, action, return}

    # ── Execution ──
    execution_result: dict | None       # Fill price, fees, slippage

    # ── Portfolio Context ──
    portfolio_state: dict               # Current positions, cash, P&L

    # ── Agent Messages (for LangGraph tool calling) ──
    messages: list                      # MessagesState for tool calls

    # ── Post-Execution Reflection (CryptoTrade Level 2 + TradingAgents memory) ──
    post_reflection_notes: str | None   # Post-trade learning
    cross_trial_memories: list[str]     # Sliding window of 3 (from CryptoTrade)
```

---

## 11. Reflection & Memory System

Combines TradingAgents' per-agent memory system with CryptoTrade's proven two-level reflection (the second most valuable component per ablation: -11.33% when removed).

### Two-Level Reflection Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                    LEVEL 1: IN-CONTEXT REFLECTION                │
│                    (from CryptoTrade, runs every cycle)          │
│                                                                  │
│  Input: Last N decisions with reasoning, actions, and returns    │
│                                                                  │
│  Prompt (adapted from CryptoTrade's env_history.py):             │
│  "Your analysis and action history is given in chronological     │
│   order: [REASONING, ACTION, DAILY RETURN for each cycle]...     │
│   Reflect on recent performance. Identify what information       │
│   was most impactful. Assess whether a more aggressive or        │
│   conservative approach is warranted."                           │
│                                                                  │
│  Output: Strategic guidance injected into trader's next prompt   │
│                                                                  │
│  Extension beyond CryptoTrade:                                   │
│  We split this across ALL agent roles (TradingAgents pattern):   │
│  - bull_memory:  "My bullish thesis on X was correct/wrong..."   │
│  - bear_memory:  "I missed the risk of Y / correctly flagged..." │
│  - trader_memory: "Sizing was too aggressive given regime..."    │
│  - risk_memory:  "Stop loss was appropriate / should be tighter" │
│  - onchain_memory: "Whale signal was predictive / false alarm"   │
└──────────────────────────────────────────────────────────────────┘
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                LEVEL 2: CROSS-TRIAL MEMORY                       │
│                (from CryptoTrade's generate_reflections.py)      │
│                                                                  │
│  Trigger: After unsuccessful periods (e.g., weekly if losing)    │
│                                                                  │
│  Prompt (from CryptoTrade):                                      │
│  "You will be given the history of a past experience in which    │
│   you were placed in an environment and given a task to          │
│   complete. You were unsuccessful... Devise a concise, new plan  │
│   of action that accounts for your mistake with reference to     │
│   specific actions that you should have taken."                  │
│                                                                  │
│  Memory: Sliding window of last 3 reflections (same as          │
│  CryptoTrade) prepended to future decision contexts              │
│                                                                  │
│  Extension beyond CryptoTrade:                                   │
│  - Also generate reflections after SUCCESSFUL periods            │
│    ("What worked and should be repeated?")                       │
│  - Per-agent reflections, not just global                        │
│  - Include market regime context in reflection                   │
└──────────────────────────────────────────────────────────────────┘
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                LEVEL 3: STRATEGY ADAPTATION (NEW)                │
│                (not in either framework)                          │
│                                                                  │
│  Trigger: Monthly or after significant drawdown                  │
│                                                                  │
│  Actions:                                                        │
│  - Regime detector recalibrates based on accuracy history        │
│  - Position sizing parameters adjust based on win rate           │
│  - Confidence thresholds shift based on performance              │
│  - Data source weighting adjusts (if on-chain signals are        │
│    underperforming, shift weight to sentiment, and vice versa)   │
└──────────────────────────────────────────────────────────────────┘
```

### Memory Storage

```
memory/
├── agent_memories/
│   ├── bull_researcher.json     # Persistent bull argument history + outcomes
│   ├── bear_researcher.json     # Persistent bear argument history + outcomes
│   ├── trader.json              # Decision history + P&L attribution
│   ├── risk_manager.json        # Risk assessment accuracy log
│   └── onchain_analyst.json     # Signal accuracy log
├── trade_log.db                 # SQLite: all trades, fills, P&L
├── reflections.db               # SQLite: all reflection outputs
└── regime_history.json          # Regime classifications + accuracy
```

---

## 12. Historical Signal Correlation Engine

**Purpose:** Before the agent trades live, we need to understand which signals actually predicted price movements historically. This is the "ground-up research" layer that feeds the reasoning LLM with empirically-validated signal weights.

### Multi-Timeframe Signal Database

```
signal_correlation/
├── __init__.py
├── signal_store.py          # Store all signals with timestamps
├── price_store.py           # Historical OHLCV at all granularities
├── correlation_engine.py    # Compute signal → price correlations
├── report_generator.py      # Generate correlation reports for LLM context
└── weight_optimizer.py      # Adjust signal weights based on accuracy
```

### How It Works

```
Step 1: COLLECT all signals over historical periods
  For each token of interest, store every signal the system generates:
  - On-chain analyst signals (whale movements, exchange flows, tx stats)
  - Technical analyst signals (RSI, MACD, BB, funding rate direction)
  - Sentiment analyst signals (social score, news sentiment, Fear & Greed)
  - Protocol analyst signals (TVL trend, unlock events, governance)
  - Macro signals (M2 trend, DXY direction, Fed rate expectations)
  - Insider signals (whale accumulation, congress trades, VC moves)

Step 2: COMPARE against actual price action at multiple timeframes
  For each signal emitted at time T, measure what happened to price:
  ┌──────────────────────────────────────────────────────┐
  │ Timeframe │ Measure                                   │
  ├───────────┼───────────────────────────────────────────┤
  │ 4 hours   │ Price change T → T+4h                     │
  │ Daily     │ Price change T → T+24h                    │
  │ Weekly    │ Price change T → T+7d                     │
  │ Monthly   │ Price change T → T+30d                    │
  └──────────────────────────────────────────────────────┘

Step 3: COMPUTE correlations and predictive accuracy
  For each signal type at each timeframe:
  - Hit rate: % of times signal direction matched price direction
  - Magnitude correlation: did stronger signals predict bigger moves?
  - Lag analysis: does the signal lead price by N hours/days?
  - False positive rate: how often did the signal fire without price movement?

Step 4: IDENTIFY cross-signal patterns
  The reasoning LLM receives a concise correlation matrix and looks for:
  - Signal confluence: when 3+ signals align, what's the hit rate?
  - Inverse correlations: signals that move opposite to each other
  - Regime-dependent accuracy: which signals work in bull vs bear vs sideways?
  - Macro overlay: do signals perform better/worse during specific M2/DXY regimes?

Step 5: WEIGHT signals dynamically
  Feed the correlation analysis to the reasoning LLM:
  "Given these historical accuracy metrics across timeframes, which signals
   should we weight most heavily for the current market regime? Are there
   correlations or inverse-correlations that suggest a combined signal
   is more predictive than any individual one?"
```

### Correlation Report Format (fed to reasoning LLM)

```
SIGNAL CORRELATION REPORT for {TOKEN} | Generated: {date}
Current macro regime: {M2 expanding/contracting} | DXY: {rising/falling} | Fed: {hawkish/dovish}

SIGNAL ACCURACY BY TIMEFRAME (last 90 days):
┌─────────────────────┬──────────┬─────────┬──────────┬──────────┐
│ Signal              │ 4h acc.  │ Daily   │ Weekly   │ Monthly  │
├─────────────────────┼──────────┼─────────┼──────────┼──────────┤
│ Whale accumulation  │ 52%      │ 61%     │ 73%      │ 78%      │
│ Exchange outflows   │ 54%      │ 58%     │ 67%      │ 71%      │
│ RSI oversold/overbought │ 63% │ 57%     │ 49%      │ 45%      │
│ Funding rate extreme│ 68%      │ 62%     │ 55%      │ 48%      │
│ CT sentiment spike  │ 45%      │ 48%     │ 42%      │ 40%      │
│ Congress buy signal │ N/A      │ N/A     │ 64%      │ 69%      │
│ M2 expansion (90d lag) │ N/A   │ N/A     │ 71%      │ 82%      │
│ DXY reversal        │ N/A      │ 55%     │ 68%      │ 75%      │
└─────────────────────┴──────────┴─────────┴──────────┴──────────┘

CONFLUENCE PATTERNS:
- Whale accumulation + exchange outflows + M2 expanding → 87% weekly accuracy
- RSI oversold + funding rate negative → 72% 4h bounce accuracy
- Congress buy + whale buy + M2 expanding → 91% monthly accuracy

INVERSE CORRELATIONS:
- CT sentiment spike has NEGATIVE 30d correlation (-0.23) → fade retail hype
- High funding rate + whale selling → 78% accuracy for 4h-daily correction
```

### Key Insight for Implementation

The reasoning LLM doesn't just receive raw signals -- it receives this **pre-computed accuracy matrix** as context. This allows it to dynamically weight its own analysis: "Whale accumulation has 78% monthly accuracy in the current M2-expanding regime, so I'll weight this heavily in my long-term thesis."

This is what differentiates our approach: **empirically-validated, regime-aware signal weighting** that adapts over time as the correlation engine updates.

---

## 13. Macro & Insider Intelligence Layer

### Macro Signals

Crypto prices are heavily influenced by macroeconomic conditions. Precise numbers from econometric analysis:

**M2-Bitcoin relationship (cointegration analysis, 2015-2025):**
- **Long-run elasticity: 2.65** -- a 1% increase in M2 → 2.65% increase in BTC price
- Error correction: 12% of deviations corrected monthly
- 180-day rolling Pearson correlation **oscillates between +0.95 and -0.90** (structural periodicity, NOT constant)
- Post-ETF (Jan 2024+): stabilized ~0.65, but weakening
- The 90-day lag is a central tendency, not a precise clock. Other factors (ETF flows, policy surprises) modulate it significantly

**DXY-Bitcoin relationship:**
- Inverse correlation: approximately -0.58
- DXY lag for strongest correlation: ~33 days (1 month)
- Remained more stable through regime changes than M2 correlation

**Key insight for implementation:** M2 is a directional bias indicator (expanding = bullish, contracting = bearish), NOT a timing signal. Weight more heavily at weekly/monthly timeframes.

```
dataflows/
├── macro/                         # NEW: Macroeconomic data
│   ├── m2_money_supply.py         # Global M2 (Fed, ECB, PBoC, BoJ)
│   ├── dxy_index.py               # US Dollar Index
│   ├── fed_rates.py               # Federal funds rate + expectations
│   ├── treasury_yields.py         # 2Y/10Y yields, yield curve
│   ├── global_liquidity.py        # Combined liquidity index
│   └── macro_regime.py            # Classify: risk-on / risk-off / transition
│
├── insider/                       # NEW: Smart money / insider signals
│   ├── congress_trades.py         # US Congress trades (Quiver Quantitative API)
│   ├── whale_wallets.py           # Named whale wallet tracking (Arkham/Nansen)
│   ├── vc_movements.py            # VC fund wallet movements (a16z, Paradigm, etc.)
│   ├── exchange_insider.py        # Exchange reserve changes + large OTC signals
│   └── token_insider.py           # Team/founder wallet movements, vesting claims
```

### Macro Data Sources

| Signal | Source | Update Frequency | Lag to Crypto Impact |
|--------|--------|-----------------|---------------------|
| Global M2 | FRED API (Fed), ECB, PBoC, BoJ data | Weekly | ~90 days central tendency (oscillates, 2.65x elasticity) |
| DXY | FRED API / TradingView | Daily | ~33 days for strongest inverse correlation (-0.58) |
| Fed Funds Rate | FRED API | Per FOMC meeting | Immediate (announcement) |
| Fed Expectations | CME FedWatch | Daily | Priced in continuously |
| Treasury Yields | FRED API | Daily | ~1-7 days |
| CPI / Inflation | BLS.gov | Monthly | Immediate to 1 week |

### Insider Signal Sources

| Signal | Source | Access | Reliability |
|--------|--------|--------|-------------|
| US Congress trades | [Quiver Quantitative API](https://www.quiverquant.com/congresstrading/) | API (paid tier for real-time) | HIGH -- legally required disclosures, 45-day reporting lag |
| Whale wallets (named) | [Arkham Intelligence](https://www.arkham.com/) | API (free tier + paid) | HIGH -- entity identification across 10+ chains |
| Whale wallets (behavioral) | [Nansen](https://www.nansen.ai/api) | API (paid) | HIGH -- Smart Money labels, win rate tracking |
| VC fund wallets | Arkham + custom tracking | API + manual curation | MEDIUM -- VCs may use multiple wallets |
| Exchange reserves | CryptoQuant / Glassnode | API (paid) | HIGH -- exchange cold wallet monitoring |
| Team/founder wallets | Manual curation + Arkham | Mixed | MEDIUM -- depends on wallet identification |

### Macro Analyst Agent (NEW -- added to Phase 1 analysts)

```
Role: Analyze macroeconomic conditions to determine risk environment for crypto

Inputs:
  - Global M2 money supply trend (weekly, with 90-day lead indicator)
  - DXY direction and key levels (inverse correlation with BTC)
  - Fed rate expectations (CME FedWatch probabilities)
  - Treasury yield curve (2Y/10Y spread -- inversion = risk-off)
  - Recent CPI/inflation prints
  - Global liquidity index (cross-central-bank composite)

Output: Macro environment report
  - Risk regime: risk-on / risk-off / transitioning
  - Liquidity direction: expanding / contracting / neutral
  - Key upcoming catalysts (FOMC dates, CPI release, etc.)
  - Historical pattern match: "current M2/DXY combo most resembles [period],
    which saw crypto [outcome]"
  - Recommended position sizing modifier (e.g., "macro tailwind: +20% sizing"
    or "macro headwind: -30% sizing")
```

### Insider Analyst Agent (NEW -- added to Phase 1 analysts)

```
Role: Track smart money movements and institutional/political insider activity

Inputs:
  - Congress member trades (last 30 days, filtered for crypto-adjacent stocks
    and direct crypto holdings)
  - Whale wallet movements for target token (Arkham/Nansen labeled wallets)
  - VC fund wallet activity (accumulation/distribution patterns)
  - Team/founder wallet claims and movements
  - Exchange reserve changes (large inflows = potential sell pressure)

Output: Insider signal report
  - Whale consensus: accumulating / distributing / neutral
  - Congress signal: buying / selling / no activity
  - VC signal: deploying / harvesting / holding
  - Team risk: any founder selling / vesting unlocks claimed
  - Historical accuracy note: "whale accumulation signals have had {X}% weekly
    accuracy for this token over the past 90 days"
```

### Integration with Signal Correlation Engine

Both macro and insider signals feed into the correlation engine (Section 12). The reasoning LLM receives not just the current signals but their historical accuracy:

```
The reasoning LLM's context includes:
1. Current macro state: "M2 expanding, DXY falling, Fed expected to cut in 60 days"
2. Historical pattern: "This macro configuration has preceded crypto rallies 82% of the time"
3. Current insider state: "3 Congress members bought crypto-adjacent stocks, whales accumulated 2.1M tokens"
4. Historical accuracy: "Congress + whale confluence has 91% monthly directional accuracy"
5. Signal correlation matrix at the current timeframe of interest
```

---

## 14. Multi-Strategy Parallel Execution

**Purpose:** Different timeframes and strategies perform differently under different market conditions. Rather than guessing which will work, we run multiple strategies in parallel and let performance data guide capital allocation over time.

### Strategy Runner Architecture

```
strategies/
├── __init__.py
├── strategy_config.py           # Strategy definition schema
├── strategy_runner.py           # Parallel strategy orchestrator
├── strategy_comparator.py       # Live performance comparison
├── capital_allocator.py         # Dynamic allocation based on performance
│
├── presets/                     # Pre-built strategy configurations
│   ├── conservative_weekly.yaml
│   ├── balanced_daily.yaml
│   ├── aggressive_4h.yaml
│   ├── moonshot_daily.yaml
│   └── macro_monthly.yaml
```

### Strategy Configuration Schema

Each strategy is a complete configuration that defines how a separate instance of the agent pipeline operates:

```python
@dataclass
class StrategyConfig:
    # Identity
    name: str                          # e.g., "conservative_weekly"
    description: str

    # Timeframe
    decision_frequency: str            # "4h" | "daily" | "weekly" | "monthly"
    candle_timeframe: str              # Which candles the technical analyst uses
    lookback_window: int               # How many candles of history to analyze

    # Risk Profile
    risk_profile: str                  # "conservative" | "balanced" | "aggressive" | "moonshot"
    max_position_size_pct: float       # Max % of strategy capital per position
    max_total_exposure_pct: float      # Max % of strategy capital deployed
    stop_loss_pct: float               # Default stop-loss %
    take_profit_targets: list[float]   # TP levels [0.05, 0.10, 0.20]
    max_daily_loss_pct: float          # Circuit breaker
    min_risk_reward_ratio: float       # Minimum R:R to enter a trade

    # Token Universe
    token_universe: list[str]          # Which tokens this strategy can trade
    chain_filter: list[str]            # Which chains (or "all")

    # Signal Weighting (informed by correlation engine)
    signal_weights: dict               # Override default weights per signal type
    min_confluence_signals: int        # Minimum aligned signals to enter

    # LLM Configuration
    deep_think_model: str              # Model for reasoning-heavy tasks
    quick_think_model: str             # Model for data summarization
    max_debate_rounds: int             # Bull/bear debate depth

    # Capital Allocation
    allocated_capital_pct: float       # % of total portfolio allocated to this strategy
    rebalance_frequency: str           # How often to rebalance capital between strategies

    # Wealth Target
    target_return_pct: float | None    # Target return (e.g., 50% annual)
    target_timeline_months: int | None # Timeline to achieve target
```

### Parallel Execution Model

```
┌─────────────────────────────────────────────────────────────┐
│                   STRATEGY ORCHESTRATOR                      │
│                                                              │
│  Total Portfolio: $10,000                                    │
│                                                              │
│  ┌──────────────────────┐  ┌──────────────────────┐         │
│  │ Strategy A            │  │ Strategy B            │        │
│  │ "Conservative Weekly" │  │ "Balanced Daily"      │        │
│  │ Capital: $4,000 (40%) │  │ Capital: $3,000 (30%) │        │
│  │ Frequency: Weekly     │  │ Frequency: Daily      │        │
│  │ Tokens: BTC,ETH,SOL  │  │ Tokens: Mid-caps      │        │
│  │ Max loss: -5%/week    │  │ Max loss: -3%/day     │        │
│  │ Target: 20% annual    │  │ Target: 40% annual    │        │
│  │                       │  │                       │        │
│  │ ┌─────────────────┐  │  │ ┌─────────────────┐   │        │
│  │ │ Full Agent       │  │  │ │ Full Agent       │  │        │
│  │ │ Pipeline         │  │  │ │ Pipeline         │  │        │
│  │ │ (own graph run)  │  │  │ │ (own graph run)  │  │        │
│  │ └─────────────────┘  │  │ └─────────────────┘   │        │
│  └──────────────────────┘  └──────────────────────┘         │
│                                                              │
│  ┌──────────────────────┐  ┌──────────────────────┐         │
│  │ Strategy C            │  │ Strategy D            │        │
│  │ "Aggressive 4h"       │  │ "Moonshot"            │        │
│  │ Capital: $2,000 (20%) │  │ Capital: $1,000 (10%) │        │
│  │ Frequency: 4 hours    │  │ Frequency: Daily      │        │
│  │ Tokens: Trending alts │  │ Tokens: Low-cap gems  │        │
│  │ Max loss: -5%/day     │  │ Max loss: -90% total  │        │
│  │ Target: 100% annual   │  │ Target: 10x or bust   │        │
│  │                       │  │                       │        │
│  │ ┌─────────────────┐  │  │ ┌─────────────────┐   │        │
│  │ │ Full Agent       │  │  │ │ Full Agent       │  │        │
│  │ │ Pipeline         │  │  │ │ Pipeline         │  │        │
│  │ │ (own graph run)  │  │  │ │ (own graph run)  │  │        │
│  │ └─────────────────┘  │  │ └─────────────────┘   │        │
│  └──────────────────────┘  └──────────────────────┘         │
│                                                              │
│  ┌──────────────────────────────────────────────────┐       │
│  │ STRATEGY COMPARATOR                               │       │
│  │ Tracks: Sharpe, return, drawdown, win rate        │       │
│  │ Per strategy, per timeframe, per market regime    │       │
│  │                                                    │       │
│  │ CAPITAL ALLOCATOR                                  │       │
│  │ Quarterly rebalance: shift capital toward          │       │
│  │ best-performing strategies, reduce underperformers │       │
│  └──────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────┘
```

### Key Design Decisions

**Each strategy runs its OWN full agent pipeline** -- separate analysts, debate, trader, risk gate. This is critical because:
- A weekly strategy needs weekly candle analysis, not 4h noise
- A moonshot strategy should have an aggressive risk gate, not conservative
- Signal weights differ: weekly strategies weight macro/whale signals higher; 4h strategies weight funding rates/RSI higher (per correlation engine data)

**Strategies share the data layer** -- One DataAggregator feeds all strategies. Data is cached at the finest granularity (1h) and aggregated up for coarser timeframes.

**Strategies have isolated capital** -- One strategy's drawdown doesn't affect another's available capital. This prevents a moonshot bet from jeopardizing the conservative allocation.

**The comparator runs continuously** -- Every strategy's performance is tracked in real-time against its benchmark, and a weekly performance report is generated showing which strategies are working in the current market regime.

---

## 15. Risk Profile Configurations

### Pre-Built Strategy Presets

#### Conservative Weekly (Wealth Preservation)
```yaml
name: conservative_weekly
description: "Long-term accumulation on weekly candles. Low risk, steady growth."
decision_frequency: weekly
candle_timeframe: 1w
lookback_window: 26  # 6 months of weekly candles
risk_profile: conservative
max_position_size_pct: 15
max_total_exposure_pct: 50  # 50% always in stables
stop_loss_pct: 8
take_profit_targets: [0.15, 0.25, 0.40]
max_daily_loss_pct: 3  # very tight circuit breaker
min_risk_reward_ratio: 2.0
token_universe: [BTC, ETH, SOL, AAVE, LINK, UNI]  # large caps only
signal_weights:
  macro_signals: 0.30        # M2, DXY heavily weighted for weekly
  whale_insider: 0.25        # Congress, whale accumulation (high weekly accuracy)
  onchain_stats: 0.20        # Network health
  technical: 0.15            # Weekly RSI, moving averages
  sentiment: 0.10            # Less noise at weekly scale
min_confluence_signals: 3
allocated_capital_pct: 40
target_return_pct: 20
target_timeline_months: 12
```

#### Balanced Daily (Core Strategy)
```yaml
name: balanced_daily
description: "Daily swing trading on mid-caps. Moderate risk, aims for alpha."
decision_frequency: daily
candle_timeframe: 1d
lookback_window: 30  # 30 days of daily candles
risk_profile: balanced
max_position_size_pct: 10
max_total_exposure_pct: 70
stop_loss_pct: 5
take_profit_targets: [0.08, 0.15, 0.25]
max_daily_loss_pct: 3
min_risk_reward_ratio: 1.5
token_universe: [ARB, OP, AAVE, MKR, SNX, PENDLE, GMX, DYDX, INJ, TIA]
signal_weights:
  onchain_stats: 0.25
  technical: 0.25
  macro_signals: 0.20
  whale_insider: 0.15
  sentiment: 0.15
min_confluence_signals: 3
allocated_capital_pct: 30
target_return_pct: 40
target_timeline_months: 12
```

#### Aggressive 4h (Active Trading)
```yaml
name: aggressive_4h
description: "4-hour swing trades on trending tokens. Higher risk, higher reward."
decision_frequency: 4h
candle_timeframe: 4h
lookback_window: 42  # 7 days of 4h candles
risk_profile: aggressive
max_position_size_pct: 15
max_total_exposure_pct: 80
stop_loss_pct: 3
take_profit_targets: [0.05, 0.10, 0.18]
max_daily_loss_pct: 5
min_risk_reward_ratio: 1.2
token_universe: dynamic  # Selected by research agent based on momentum
signal_weights:
  technical: 0.35            # RSI, funding rate dominate at 4h
  onchain_stats: 0.25
  sentiment: 0.20            # CT hype can move 4h candles
  whale_insider: 0.10
  macro_signals: 0.10        # Macro less relevant at 4h scale
min_confluence_signals: 2
allocated_capital_pct: 20
target_return_pct: 100
target_timeline_months: 12
```

#### Moonshot (Asymmetric Bets)
```yaml
name: moonshot
description: "High-conviction asymmetric bets. Expect 90% to fail, 1 to 10x."
decision_frequency: daily
candle_timeframe: 1d
lookback_window: 14
risk_profile: moonshot
max_position_size_pct: 20  # Concentrated positions
max_total_exposure_pct: 100  # Can go all-in
stop_loss_pct: 50  # Wide stops -- let it breathe or die
take_profit_targets: [1.0, 3.0, 10.0]  # 2x, 4x, 11x targets
max_daily_loss_pct: 100  # No daily circuit breaker -- accept full loss
min_risk_reward_ratio: 5.0  # Only enter if potential is 5x+
token_universe: dynamic  # New narratives, low-cap gems, early DeFi
chain_filter: [solana, base, arbitrum]  # Where new projects launch
signal_weights:
  onchain_stats: 0.30        # Early whale accumulation is key
  sentiment: 0.25            # Narrative momentum matters for moonshots
  whale_insider: 0.25        # Smart money entering early
  technical: 0.10            # Less relevant for early-stage tokens
  macro_signals: 0.10        # Bull market helps but isn't the thesis
min_confluence_signals: 2
allocated_capital_pct: 10    # BARBELL: only 10% of total portfolio
target_return_pct: 1000      # Targeting 10x on at least one position
target_timeline_months: 6
special_rules:
  - "Only enter tokens with < $100M market cap"
  - "Require at least 2 whale wallets accumulating"
  - "Must have active developer commits in last 30 days"
  - "Auto-sell 50% at 3x, let rest ride with trailing stop"
```

#### Macro Monthly (Big Picture)
```yaml
name: macro_monthly
description: "Monthly rebalancing based on macro conditions. Lowest maintenance."
decision_frequency: monthly
candle_timeframe: 1M
lookback_window: 12  # 12 months of monthly candles
risk_profile: conservative
max_position_size_pct: 25
max_total_exposure_pct: 60
stop_loss_pct: 15
take_profit_targets: [0.30, 0.50, 1.00]
min_risk_reward_ratio: 2.5
token_universe: [BTC, ETH, SOL]  # Only majors
signal_weights:
  macro_signals: 0.50         # M2/DXY/Fed dominate at monthly scale
  whale_insider: 0.20         # Congress trades, institutional flows
  onchain_stats: 0.15
  technical: 0.10
  sentiment: 0.05
min_confluence_signals: 2
allocated_capital_pct: 0      # Optional -- user enables if desired
target_return_pct: 30
target_timeline_months: 12
```

### The Barbell Portfolio Structure

The preset allocations follow a barbell strategy (Nassim Taleb's approach applied to crypto):

```
SAFE SIDE (70%):                              RISK SIDE (30%):
┌─────────────────────────────┐              ┌─────────────────────────┐
│ Conservative Weekly    40%  │              │ Aggressive 4h       20% │
│ Balanced Daily         30%  │              │ Moonshot             10% │
│                             │              │                         │
│ Max expected loss: ~15%     │              │ Max expected loss: ~90% │
│ Expected return: 20-40%/yr  │              │ Possible return: 10x+   │
└─────────────────────────────┘              └─────────────────────────┘

Net portfolio: If safe side returns 25% and risk side loses 50%:
  (0.70 × 1.25) + (0.30 × 0.50) = 0.875 + 0.15 = 1.025 → +2.5%

If safe side returns 25% and ONE moonshot hits 10x:
  (0.70 × 1.25) + (0.20 × 0.50) + (0.10 × 10.0) = 0.875 + 0.10 + 1.0 = 1.975 → +97.5%
```

### Dynamic Capital Reallocation

Every quarter (or configurable), the Strategy Comparator evaluates all running strategies:

```python
class CapitalAllocator:
    def rebalance(self, strategy_results: dict, market_regime: str):
        """
        Shift capital toward best-performing strategies based on:
        1. Sharpe ratio over evaluation period
        2. Performance relative to strategy's own target
        3. Current market regime (may favor different strategies)

        Rules:
        - Never reduce moonshot below 5% (maintain asymmetric exposure)
        - Never increase any single strategy above 50%
        - Rebalancing must be gradual (max 10% shift per quarter)
        - If ALL strategies are underperforming, increase stables allocation
        """
```

---

## 16. Risk Management

### Multi-Layer Risk Controls

```
Layer 1: POSITION-LEVEL (per trade)
  - Max position size: 10% of portfolio (configurable)
  - Required stop loss on every trade
  - Minimum risk/reward ratio: 1.5x
  - Slippage pre-check: reject if estimated slippage > 2%

Layer 2: PORTFOLIO-LEVEL (across all positions)
  - Max total exposure: 70% of portfolio (30% always in stables)
  - Max sector concentration: 30% (e.g., DeFi, L2s, AI tokens)
  - Max chain concentration: 40% on any single chain
  - Correlation check: don't open correlated positions simultaneously

Layer 3: REGIME-LEVEL (market conditions)
  - BULL regime:   max exposure 70%, normal sizing
  - SIDEWAYS:      max exposure 50%, reduced sizing
  - BEAR regime:   max exposure 30%, minimum sizing, short-bias allowed
  - CRASH regime:  max exposure 10%, close most positions, capital preservation
  - EUPHORIA:      max exposure 40%, take profits aggressively

Layer 4: CIRCUIT BREAKERS (hard limits, no AI override)
  - Daily loss limit: -5% of portfolio -> halt all trading for 24h
  - Weekly loss limit: -10% of portfolio -> halt for 72h + alert
  - Single trade max loss: -3% of portfolio -> force close
  - API error rate > 5% -> pause execution, alert
```

### Smart Contract Risk Assessment

For DEX trades, before execution:
- Check if contract is verified on block explorer
- Check if protocol has been audited (audit registry)
- Check contract age (reject < 30 days unless manually whitelisted)
- Check TVL (reject if < $1M TVL)
- Check for recent exploit reports

---

## 17. Decoupled Risk Sentinel (from WebCryptoAgent)

**Problem:** Our LangGraph pipeline takes 2-5 minutes per decision cycle. But market crashes happen in seconds. The pipeline's circuit breakers only activate AFTER a full cycle completes -- too slow for flash crashes.

**Solution (from WebCryptoAgent, arXiv: 2601.04687):** A decoupled control architecture that separates strategic reasoning from real-time risk monitoring.

```
┌─────────────────────────────────────────────────────────────────┐
│                    DECOUPLED CONTROL ARCHITECTURE                │
│                                                                  │
│  SLOW PATH (minutes):              FAST PATH (seconds):         │
│  ┌─────────────────────┐           ┌─────────────────────────┐  │
│  │ LangGraph Pipeline  │           │ RISK SENTINEL           │  │
│  │                     │           │                         │  │
│  │ Analysts → Debate → │           │ Runs independently      │  │
│  │ Trader → Risk Gate  │           │ Monitors:               │  │
│  │                     │           │  - Price feeds (1s)     │  │
│  │ Output: Trade       │           │  - Liquidation cascades │  │
│  │ decisions every     │           │  - Volume anomalies     │  │
│  │ 4h/daily/weekly     │           │  - Flash crash detect   │  │
│  │                     │  OVERRIDE │  - Stablecoin depeg     │  │
│  │ ┌─────────────────┐ │ ◄────────│                         │  │
│  │ │ Executor        │ │           │ Can:                    │  │
│  │ │ (can be halted) │ │           │  - HALT all execution   │  │
│  │ └─────────────────┘ │           │  - Close positions      │  │
│  └─────────────────────┘           │  - Tighten stop-losses  │  │
│                                    │  - Alert immediately    │  │
│                                    └─────────────────────────┘  │
│                                                                  │
│  The sentinel runs as a SEPARATE process/thread, NOT inside     │
│  the LangGraph graph. It has direct access to the executor      │
│  and can override any pending trade.                             │
└─────────────────────────────────────────────────────────────────┘
```

### Risk Sentinel Implementation

```python
class RiskSentinel:
    """
    Lightweight, always-on risk monitor running independently of the
    LangGraph pipeline. Inspired by WebCryptoAgent's decoupled control.

    Monitors real-time price feeds and can halt/override execution
    within seconds, vs the pipeline's minutes-long decision cycle.
    """

    def __init__(self, executor: ExecutionRouter, config: SentinelConfig):
        self.executor = executor
        self.config = config
        self.running = True

    async def monitor_loop(self):
        """Runs every 1-5 seconds, independent of trading pipeline."""
        while self.running:
            # Fast checks (no LLM calls -- pure numeric thresholds)
            price_data = await self.get_latest_prices()  # WebSocket feed

            # 1. Flash crash detection
            if self.detect_flash_crash(price_data):
                await self.emergency_action("HALT_ALL", reason="Flash crash detected")

            # 2. Portfolio drawdown check
            if self.current_drawdown() > self.config.max_drawdown_pct:
                await self.emergency_action("CLOSE_ALL", reason="Max drawdown breached")

            # 3. Stablecoin depeg detection (USDT, USDC)
            if self.detect_stablecoin_depeg(price_data):
                await self.emergency_action("CONVERT_TO_FIAT", reason="Stablecoin depeg")

            # 4. Abnormal volume spike (potential manipulation)
            if self.detect_volume_anomaly(price_data):
                await self.tighten_stop_losses(factor=0.5)

            await asyncio.sleep(self.config.check_interval_seconds)  # 1-5s

    async def emergency_action(self, action: str, reason: str):
        """Execute emergency action, bypass LangGraph entirely."""
        self.executor.halt()  # Immediately stop all pending orders
        self.notify_emergency(action, reason)
        self.log_sentinel_action(action, reason)
```

### Sentinel vs Circuit Breakers

| Feature | Circuit Breakers (existing) | Risk Sentinel (new) |
|---------|---------------------------|---------------------|
| Check frequency | Per decision cycle (4h) | Every 1-5 seconds |
| Runs inside | LangGraph pipeline | Separate process |
| Response time | Minutes | Seconds |
| Uses LLM | No | No |
| Can override pipeline | No | Yes |
| Detects | Post-hoc losses | Real-time anomalies |

Both coexist: circuit breakers handle slower-moving risk (daily/weekly loss limits), while the sentinel handles second-level emergencies.

---

## 18. Fact-Subjectivity Aware Reasoning (from FS-ReasoningAgent)

**Problem:** FS-ReasoningAgent (NUS, arXiv: 2410.12464) discovered that stronger LLMs sometimes underperform weaker ones in crypto trading because they over-weight factual data and under-weight subjective signals. Their key finding: **separating factual and subjective reasoning improves profits by 7-10%.**

**Critical regime dependency:**
- **Bull markets:** Subjective signals (narrative momentum, social hype, FOMO) generate higher returns
- **Bear markets:** Factual signals (on-chain data, fundamentals, technicals) yield better results

### Implementation in Our Pipeline

We add a **fact-subjectivity separation layer** to the analyst outputs before they reach the bull/bear researchers:

```python
def fact_subjectivity_processor(analyst_reports: dict, regime: str) -> dict:
    """
    Separates each analyst's output into factual and subjective components,
    then applies regime-dependent weighting.

    From FS-ReasoningAgent: this separation alone improves profits 7-10%.
    """

    # Regime-dependent weights (from FS-ReasoningAgent ablation)
    weights = {
        "bull":     {"factual": 0.40, "subjective": 0.60},  # Narrative matters more
        "euphoria": {"factual": 0.30, "subjective": 0.70},  # Peak narrative
        "sideways": {"factual": 0.55, "subjective": 0.45},  # Balanced
        "bear":     {"factual": 0.70, "subjective": 0.30},  # Facts dominate
        "crash":    {"factual": 0.80, "subjective": 0.20},  # Ignore hype
    }

    w = weights.get(regime, weights["sideways"])

    # Each analyst report is split into:
    # - Factual: on-chain data, price levels, TVL numbers, tx stats, gas, M2 readings
    # - Subjective: sentiment interpretation, narrative assessment, trend opinions
    #
    # The LLM is prompted to explicitly label each finding as [FACT] or [SUBJECTIVE]
    # in the analyst output format, then we weight them accordingly.

    return {
        "weighted_reports": apply_weights(analyst_reports, w),
        "regime_context": f"Current regime: {regime}. "
                         f"Factual weight: {w['factual']:.0%}, "
                         f"Subjective weight: {w['subjective']:.0%}",
    }
```

### Updated Analyst Prompt Pattern

All analyst prompts get this addition:

```
In your analysis, explicitly categorize each finding as:
  [FACT]: Objective, verifiable data points (prices, volumes, on-chain metrics,
          M2 readings, transaction counts, TVL numbers)
  [SUBJECTIVE]: Interpretations, sentiment readings, narrative assessments,
                trend opinions, market mood

This separation is critical -- the trader agent weights factual and subjective
signals differently depending on the current market regime.
```

---

## 19. Competitive Agent Scoring (from ContestTrade)

**Problem:** In our current design, each analyst role has ONE agent. If that agent's prompts/approach is suboptimal, there's no fallback. ContestTrade (arXiv: 2508.00554) showed that running **multiple competing agents** and selecting top performers significantly outperforms single-agent systems.

### Implementation: Agent Tournament

For critical analyst roles, we run 2-3 competing variants and score them:

```python
class AgentTournament:
    """
    Run multiple agent variants for the same role, score against
    real market feedback, and select top performer outputs.

    From ContestTrade: continuous scoring and ranking ensures
    only the best-performing agents' outputs are adopted.
    """

    def __init__(self, role: str, variants: list[AgentVariant]):
        self.role = role
        self.variants = variants
        self.scoreboard = {v.name: RunningScore() for v in variants}

    async def run_tournament(self, data: dict) -> str:
        """Run all variants in parallel, return best output."""
        results = await asyncio.gather(
            *[v.analyze(data) for v in self.variants]
        )

        # Score based on historical accuracy (from signal correlation engine)
        # Each variant's past predictions are tracked and scored
        scores = {
            v.name: self.scoreboard[v.name].weighted_score
            for v in self.variants
        }

        # Select output from top-scoring variant
        best = max(scores, key=scores.get)
        return results[self.variants.index(best)]

    def update_scores(self, actual_outcome: dict):
        """After price action is known, update all variant scores."""
        for variant in self.variants:
            predicted = variant.last_prediction
            accuracy = self.compute_accuracy(predicted, actual_outcome)
            self.scoreboard[variant.name].update(accuracy)
```

### Tournament Roles (Phase 5+)

| Role | Variant A | Variant B | Variant C |
|------|-----------|-----------|-----------|
| On-Chain Analyst | CryptoTrade-style (tx stats focus) | Whale-movement focus | Exchange flow focus |
| Technical Analyst | Momentum-based (RSI, MACD) | Mean-reversion (BB, funding) | Volume profile |
| Sentiment Analyst | CT/social-first | News-first | Fear & Greed weighted |

This is an advanced feature for Phase 5+. In early phases, we run single agents per role to keep complexity manageable.

---

## 20. Hedging Layer (from HedgeAgents)

**Problem:** HedgeAgents (WWW '25, arXiv: 2502.13165) showed that LLM agents experience -20% losses during rapid declines. Their solution: explicit cross-asset hedging coordination through structured "conferences."

### Hedging Conference (Added to Pipeline)

After the Risk Gate approves a trade but BEFORE execution, a lightweight **hedging check** runs:

```python
def hedging_check(trade_decision: TradeDecision, portfolio: Portfolio, regime: str) -> TradeDecision:
    """
    Inspired by HedgeAgents' three-conference model.
    Checks if the approved trade creates unhedged exposure
    and suggests hedging positions.

    Example: If going long $2000 in altcoins, the hedging check
    might suggest allocating $200 to a stablecoin yield position
    or maintaining a DXY-inverse position as a hedge.
    """

    # Simple hedging rules (can be LLM-enhanced later)
    hedges = []

    # 1. If total crypto exposure > 60%, suggest stablecoin hedge
    if portfolio.crypto_exposure_pct > 60:
        hedges.append(HedgeAction("increase_stables", target_pct=40))

    # 2. If concentrated in single sector (e.g., >30% DeFi), suggest diversification
    sector_concentration = portfolio.max_sector_concentration()
    if sector_concentration > 30:
        hedges.append(HedgeAction("diversify_sector", max_pct=25))

    # 3. In bear/crash regime, suggest reducing to minimum exposure
    if regime in ("bear", "crash"):
        hedges.append(HedgeAction("reduce_exposure", target_pct=30))

    # 4. For moonshot positions, ensure they don't exceed barbell allocation
    if trade_decision.risk_profile == "moonshot":
        if portfolio.moonshot_allocation_pct > 15:
            hedges.append(HedgeAction("cap_moonshot", max_pct=10))

    return trade_decision.with_hedges(hedges)
```

**HedgeAgents' results (70% annualized, 400% over 3 years) demonstrate that explicit hedging dramatically improves risk-adjusted returns.** We implement a simplified version initially and can expand to LLM-powered hedging conferences later.

---

## 21. Backtesting Harness

The hardest unsolved problem for LLM-based agents. **DeepFund (NeurIPS 2025) proved that even top LLMs lose money in real-time trading**, and **FINSABER (KDD 2026) showed that LLM advantages disappear under broad, long-term evaluation.** These findings are critical: our backtesting must account for the "time travel" problem (LLMs using future knowledge from training data) and regime-dependent behavior (too conservative in bull, too aggressive in bear).

CryptoTrade provides a starting point: their `eth_env.py` + `eth_trial.py` pattern runs the agent through historical data one day at a time, tracking portfolio state. We adopt this pattern and extend it significantly with lessons from DeepFund and FINSABER.

```
backtesting/
├── __init__.py
├── historical_data.py       # Load historical data (OHLCV, on-chain, sentiment)
├── replay_engine.py         # Feed historical data through agent graph
├── mock_execution.py        # Simulated fills with historical slippage
├── metrics.py               # Sharpe, max drawdown, win rate, etc.
└── report_generator.py      # HTML/Markdown performance reports
```

### Approach

```python
class BacktestEngine:
    """
    Replay historical data through the full agent pipeline.

    Challenges specific to LLM backtesting:
    1. LLM responses are non-deterministic -> run multiple trials, average results
    2. TIME TRAVEL PROBLEM (DeepFund, NeurIPS 2025): LLMs may have seen historical
       data during training -> use data AFTER model's training cutoff for final validation
    3. SURVIVORSHIP BIAS (FINSABER, KDD 2026): Test across broad universe and long
       periods, not just cherry-picked bull runs
    4. REGIME BIAS (FINSABER): LLM strategies are too conservative in bull, too
       aggressive in bear -> validate per-regime performance separately
    5. API costs for backtesting are high ($10-40 per run per LLM-trader-test)
       -> use cheap models (DeepSeek, local Ollama) for iteration
    6. News/sentiment data is hard to replay -> cache historical snapshots
    """

    def run(self, token, start_date, end_date, trials=3):
        for trial in range(trials):
            portfolio = VirtualPortfolio(initial_capital=10000)

            for decision_date in date_range(start_date, end_date, freq=decision_frequency):
                # Freeze data window: agent only sees data up to decision_date
                frozen_data = self.historical_data.get_window(
                    token=token,
                    end_date=decision_date,
                    lookback=lookback_period
                )

                # Run full agent pipeline with frozen data
                result = self.agent_graph.propagate(
                    token=token,
                    data_override=frozen_data,  # inject historical data
                    portfolio_state=portfolio.state()
                )

                # Simulate execution
                if result.action != "HOLD":
                    fill = self.mock_executor.execute(result, decision_date)
                    portfolio.update(fill)

            self.results.append(portfolio.final_metrics())

        return self.aggregate_results()  # Average across trials
```

### Key Metrics

- **Total return** vs buy-and-hold benchmark
- **Sharpe ratio** (risk-adjusted return)
- **Max drawdown** (worst peak-to-trough)
- **Win rate** (% of profitable trades)
- **Profit factor** (gross profit / gross loss)
- **Average trade duration**
- **Decision attribution** (which analyst contributed most to winners/losers)

---

## 22. Infrastructure & Deployment

### Development (Local)

```
- Python 3.13 + uv (package manager, same as TradingAgents)
- Redis (local, for caching)
- SQLite (trade logs, reflections, backtest data)
- Ollama (local LLM for cheap iteration, e.g., Llama 3.3 70B)
- Paper trading mode only
```

### Production

```
- VPS or cloud instance (4+ cores, 16GB RAM)
- Redis (persistent, for shared state and caching)
- PostgreSQL (trade logs, audit trail)
- LLM APIs: Claude for deep_think, DeepSeek/GPT-4o-mini for quick_think
- Monitoring: simple health checks + Telegram alerts
- Secrets: environment variables, never in code
```

### Cost Estimation (Per Decision Cycle)

```
Per token analysis (one full graph run):
  - 4 analysts (quick_think):     ~4,000 tokens input + 2,000 output each = ~24K tokens
  - 2 researchers x 2 rounds:     ~8,000 tokens input + 3,000 output each = ~44K tokens
  - Trader:                       ~6,000 tokens input + 2,000 output = ~8K tokens
  - Risk gate (3 + judge):        ~4,000 tokens input + 1,500 output each = ~22K tokens
  - Reflection:                   ~4,000 tokens input + 1,000 output = ~5K tokens

  TOTAL: ~100K tokens per decision cycle

With Claude Sonnet for quick_think ($3/M in, $15/M out) and Claude Opus for deep_think:
  - ~$0.30-0.80 per decision cycle (varies by model mix)
  - Running every 4 hours on 5 tokens = ~30 cycles/day = ~$10-25/day

With DeepSeek for quick_think and Claude Sonnet for deep_think:
  - ~$0.10-0.30 per decision cycle
  - 30 cycles/day = ~$3-9/day

USE CHEAP MODELS DURING DEVELOPMENT AND BACKTESTING.
```

---

## 23. Project Structure

```
cryptoagent/
├── README.md
├── ARCHITECTURE.md               # This document
├── pyproject.toml
├── requirements.txt
├── .env.example
│
├── cryptoagent/
│   ├── __init__.py
│   ├── default_config.py         # Extended from TradingAgents
│   │
│   ├── agents/                   # LLM-powered agent definitions
│   │   ├── __init__.py
│   │   ├── analysts/
│   │   │   ├── onchain_analyst.py
│   │   │   ├── technical_analyst.py
│   │   │   ├── sentiment_analyst.py
│   │   │   └── protocol_analyst.py
│   │   ├── researchers/
│   │   │   ├── bull_researcher.py     # Keep from TradingAgents
│   │   │   └── bear_researcher.py     # Keep from TradingAgents
│   │   ├── managers/
│   │   │   └── research_manager.py    # Keep from TradingAgents
│   │   ├── trader/
│   │   │   └── trader.py              # Extend from TradingAgents
│   │   ├── risk_mgmt/
│   │   │   ├── aggressive_analyst.py  # Keep from TradingAgents
│   │   │   ├── neutral_analyst.py     # Keep from TradingAgents
│   │   │   ├── conservative_analyst.py # Keep from TradingAgents
│   │   │   └── risk_judge.py          # Keep from TradingAgents
│   │   └── utils/
│   │       ├── prompts.py             # All system/user prompts
│   │       ├── memory.py              # Agent memory management
│   │       ├── fact_subjectivity.py   # NEW: Fact/subjective separation (FS-ReasoningAgent)
│   │       └── agent_tournament.py    # NEW: Competitive scoring (ContestTrade)
│   │
│   ├── dataflows/                # Data ingestion layer
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── aggregator.py         # Unified DataAggregator interface
│   │   ├── cache.py              # Redis/SQLite caching
│   │   ├── streaming.py          # WebSocket real-time feeds
│   │   ├── market/
│   │   │   ├── ccxt_provider.py
│   │   │   ├── funding_rates.py
│   │   │   ├── liquidations.py
│   │   │   └── dex_prices.py
│   │   ├── onchain/
│   │   │   ├── whale_tracker.py
│   │   │   ├── exchange_flows.py
│   │   │   ├── dex_volume.py
│   │   │   ├── network_stats.py
│   │   │   └── token_transfers.py
│   │   ├── social/
│   │   │   ├── twitter_sentiment.py
│   │   │   ├── reddit_monitor.py
│   │   │   ├── news_aggregator.py
│   │   │   └── fear_greed.py
│   │   └── protocol/
│   │       ├── defillama.py
│   │       ├── token_unlocks.py
│   │       ├── governance.py
│   │       └── dev_activity.py
│   │
│   ├── graph/                    # LangGraph orchestration
│   │   ├── __init__.py
│   │   ├── setup.py              # Graph construction (extend TradingAgents)
│   │   ├── trading_graph.py      # CryptoAgentGraph orchestrator
│   │   ├── conditional_logic.py  # Routing logic (keep from TradingAgents)
│   │   ├── propagation.py        # State init (modify for crypto state)
│   │   ├── reflection.py         # Post-trade reflection (extend)
│   │   ├── signal_processing.py  # Crypto signal extraction
│   │   └── regime_detector.py    # Market regime classification (NEW)
│   │
│   ├── execution/                # Trade execution (NEW)
│   │   ├── __init__.py
│   │   ├── router.py
│   │   ├── paper_trade.py
│   │   ├── cex_executor.py
│   │   ├── dex_executor.py
│   │   ├── order_manager.py
│   │   ├── position_tracker.py
│   │   └── slippage_model.py
│   │
│   ├── risk/                     # Risk management (NEW)
│   │   ├── __init__.py
│   │   ├── portfolio_limits.py
│   │   ├── circuit_breakers.py
│   │   ├── regime_rules.py
│   │   ├── contract_scanner.py
│   │   ├── risk_sentinel.py      # NEW: Decoupled real-time risk (WebCryptoAgent)
│   │   └── hedging_check.py      # NEW: Cross-asset hedging (HedgeAgents)
│   │
│   ├── llm_clients/              # Keep from TradingAgents
│   │   ├── __init__.py
│   │   └── factory.py
│   │
│   └── notifications/            # Alerts (NEW)
│       ├── telegram_bot.py
│       └── discord_webhook.py
│
├── strategies/                   # NEW: Multi-strategy parallel execution
│   ├── __init__.py
│   ├── strategy_config.py       # StrategyConfig dataclass
│   ├── strategy_runner.py       # Parallel orchestrator
│   ├── strategy_comparator.py   # Live performance comparison
│   ├── capital_allocator.py     # Dynamic rebalancing
│   └── presets/                 # Pre-built configurations
│       ├── conservative_weekly.yaml
│       ├── balanced_daily.yaml
│       ├── aggressive_4h.yaml
│       ├── moonshot_daily.yaml
│       └── macro_monthly.yaml
│
├── signal_correlation/           # NEW: Historical signal accuracy engine
│   ├── __init__.py
│   ├── signal_store.py          # Store all signals with timestamps
│   ├── price_store.py           # Historical OHLCV at all granularities
│   ├── correlation_engine.py    # Signal → price correlation analysis
│   ├── report_generator.py      # Correlation reports for LLM context
│   └── weight_optimizer.py      # Dynamic signal weight adjustment
│
├── backtesting/                  # Backtest engine (NEW)
│   ├── __init__.py
│   ├── historical_data.py
│   ├── replay_engine.py
│   ├── mock_execution.py
│   ├── metrics.py
│   └── report_generator.py
│
├── memory/                       # Persistent agent memory
│   ├── agent_memories/
│   └── trade_log.db
│
├── cli/                          # CLI interface (extend from TradingAgents)
│   └── main.py
│
└── tests/
    ├── test_agents/
    ├── test_dataflows/
    ├── test_execution/
    ├── test_graph/
    ├── test_strategies/
    ├── test_signal_correlation/
    └── test_backtesting/
```

---

## 24. Implementation Phases

### Phase 1: Foundation (Weeks 1-3)

**Goal:** Get the agent pipeline running end-to-end with paper trading on a single token.

- [ ] Fork TradingAgents, restructure to project layout above
- [ ] Replace `default_config.py` with crypto-extended config
- [ ] Implement `dataflows/market/ccxt_provider.py` (OHLCV + order book)
- [ ] Implement `onchain_analyst.py` with CryptoTrade's proven data schema (tx count, active wallets, value transferred, gas metrics) -- **ON-CHAIN FIRST per ablation priority**
- [ ] Implement `technical_analyst.py` with basic indicators (RSI, MACD, BB, funding rates)
- [ ] Stub sentiment + protocol analysts (return placeholder reports)
- [ ] Adapt LangGraph flow: fan-out analysts, keep debate + risk gate
- [ ] Implement `execution/paper_trade.py` modeled on CryptoTrade's `ETHTradingEnv` (50/50 split, fee model, ROI tracking), extended for multi-asset
- [ ] Implement basic `position_tracker.py`
- [ ] Run first end-to-end decision cycle on ETH or SOL
- [ ] Verify: all agents produce outputs, trade is "executed" in paper mode

### Phase 2: On-Chain Intelligence + Reflection + Risk Sentinel (Weeks 4-6)

**Goal:** The two highest-impact components per CryptoTrade ablation fully operational, plus real-time risk monitoring.

- [ ] Extend on-chain analyst beyond CryptoTrade baseline: add whale tracking (Dune), exchange flows, DEX volume
- [ ] Implement Level 1 reflection analyst (from CryptoTrade's `env_history.py` pattern): sliding window of recent decisions + returns, strategic guidance output
- [ ] Implement Level 2 cross-trial memory (from CryptoTrade's `generate_reflections.py`): post-period reflections, 3-memory sliding window
- [ ] Connect reflection outputs to per-agent memories (TradingAgents pattern: bull_memory, bear_memory, trader_memory, risk_memory)
- [ ] Build trade logging (SQLite)
- [ ] Add market regime detector (simple: based on BTC trend + volatility)
- [ ] Implement **Risk Sentinel** (from WebCryptoAgent): separate process monitoring price feeds every 1-5s, can halt execution independently of LangGraph pipeline
- [ ] Implement **fact-subjectivity separation** in analyst prompts (from FS-ReasoningAgent): all analysts tag findings as [FACT] or [SUBJECTIVE], regime-dependent weighting applied
- [ ] Test: run 20+ paper trade cycles, verify reflection visibly influences subsequent decisions

### Phase 3: Full Data Richness + Macro/Insider (Weeks 7-10)

**Goal:** All analysts receive real data, including macro and insider intelligence.

- [ ] Implement `social/twitter_sentiment.py` (X API v2)
- [ ] Implement `social/news_aggregator.py` (CryptoPanic or Gnews -- same sources CryptoTrade used)
- [ ] Implement `protocol/defillama.py` (TVL, fees)
- [ ] Implement `protocol/token_unlocks.py`
- [ ] Implement `macro/m2_money_supply.py` (FRED API)
- [ ] Implement `macro/dxy_index.py` (FRED API)
- [ ] Implement `macro/fed_rates.py` (FRED API + CME FedWatch)
- [ ] Implement `macro/macro_regime.py` (risk-on/risk-off classifier)
- [ ] Implement `insider/congress_trades.py` (Quiver Quantitative API)
- [ ] Implement `insider/whale_wallets.py` (Arkham Intelligence API)
- [ ] Add Macro Analyst and Insider Analyst agents to the pipeline (6 analysts total)
- [ ] Build the full `DataAggregator` interface with all methods
- [ ] Implement Redis caching layer
- [ ] All 6 analysts now receive real data

### Phase 4: Signal Correlation Engine (Weeks 11-13)

**Goal:** Build the historical signal accuracy database and correlation analysis.

- [ ] Implement `signal_correlation/signal_store.py` -- log every signal emitted by every analyst
- [ ] Implement `signal_correlation/price_store.py` -- OHLCV at 4h, daily, weekly, monthly
- [ ] Implement `signal_correlation/correlation_engine.py` -- compute accuracy by signal × timeframe
- [ ] Run initial correlation analysis on 6+ months of historical data
- [ ] Generate first Signal Correlation Report and inject into reasoning LLM context
- [ ] Identify confluence patterns: which signal combinations have highest accuracy?
- [ ] Implement regime-dependent accuracy tracking: which signals work in bull vs bear?
- [ ] Run ablation tests: disable each analyst one at a time, measure impact on paper P&L

### Phase 5: Backtesting + Multi-Timeframe Validation + Agent Tournament (Weeks 14-17)

**Goal:** Validate across timeframes and market regimes. Implement competitive agent scoring. Address DeepFund/FINSABER backtesting concerns.

- [ ] Build historical data loader (OHLCV from CCXT, snapshot on-chain/macro data)
- [ ] Build replay engine (modeled on CryptoTrade's trial-based approach)
- [ ] **Anti-time-travel validation (from DeepFund, NeurIPS 2025):** Final validation MUST use data after model's training cutoff. Historical backtests are for iteration only, not proof of performance
- [ ] **FINSABER-style broad evaluation:** Test across 10+ tokens (not just top 3) and multiple regimes to avoid survivorship bias
- [ ] Run backtests at EACH timeframe: 4h, daily, weekly, monthly
- [ ] Run across 3 market regimes (bull/sideways/bear) per CryptoTrade's evaluation methodology
- [ ] **Explicitly check for FINSABER's finding:** Are we too conservative in bull, too aggressive in bear? If so, tune regime-dependent risk parameters
- [ ] Test on BTC, ETH, SOL first (allows comparison to CryptoTrade's published numbers)
- [ ] Then test on mid-cap targets (ARB, AAVE, etc.)
- [ ] Generate performance reports (Sharpe, drawdown, win rate) per timeframe
- [ ] Identify: which timeframe is most profitable for which token under which regime?
- [ ] Compare vs baselines: buy-and-hold, simple DCA, MACD, and CryptoTrade's published results
- [ ] Target: beat CryptoTrade's bear-market protection AND improve bull-market capture
- [ ] Implement **Agent Tournament** (from ContestTrade): run 2-3 competing variants per analyst role, score against market outcomes, select top performers
- [ ] Implement **hedging check** (from HedgeAgents): lightweight hedging step between risk gate and executor

### Phase 6: Multi-Strategy Parallel Execution (Weeks 17-19)

**Goal:** Run multiple strategies simultaneously with different risk profiles.

- [ ] Implement `strategies/strategy_config.py` (StrategyConfig dataclass)
- [ ] Implement `strategies/strategy_runner.py` (parallel orchestrator)
- [ ] Create preset YAML configs: conservative_weekly, balanced_daily, aggressive_4h, moonshot
- [ ] Each strategy runs its own full agent pipeline with isolated capital
- [ ] Implement `strategies/strategy_comparator.py` (live performance tracking)
- [ ] Implement `strategies/capital_allocator.py` (quarterly rebalancing logic)
- [ ] Run all 4 strategies in parallel on paper trading for 30+ days
- [ ] Generate comparative performance report: which strategy won in current regime?
- [ ] Tune signal weights per strategy based on correlation engine data

### Phase 7: Multi-Token & Multi-Chain (Weeks 20-22)

**Goal:** Run simultaneously on multiple tokens across chains.

- [ ] Token universe selection logic (which tokens to analyze)
- [ ] Parallel graph execution for multiple tokens
- [ ] Portfolio-level risk management (cross-position)
- [ ] Chain-specific execution routing
- [ ] Portfolio rebalancing logic

### Phase 8: Live Execution (Weeks 23+)

**Goal:** Graduate from paper to real trading with small capital.

- [ ] Implement `cex_executor.py` with CCXT
- [ ] Implement `dex_executor.py` for primary chain (e.g., Ethereum via 1inch)
- [ ] Circuit breakers and hard limits
- [ ] Telegram notification bot
- [ ] Deploy to VPS
- [ ] Start with $500-1000 max allocation
- [ ] Monitor for 30+ days before scaling

---

## 25. Key Technical Decisions

### LLM Selection Strategy

| Role | Recommended Model | Why |
|------|------------------|-----|
| Analysts (quick_think) | DeepSeek V3 or GPT-4.1-mini | Cost efficiency, fast, good enough for data summarization |
| Researchers (deep_think) | Claude Sonnet 4.6 | Strong reasoning, good at argumentation |
| Trader (deep_think) | Claude Sonnet 4.6 | Critical decision point, needs strong synthesis |
| Risk Judge (deep_think) | Claude Sonnet 4.6 | Must catch what others miss |
| Reflection | DeepSeek V3 | Cost efficiency, runs frequently |
| Backtesting | Ollama (Llama 3.3 70B) | Free, runs locally, acceptable for iteration |

### Decision Frequency

- **Default:** Every 4 hours (6 decisions/day per token)
- **High volatility:** Every 1 hour (triggered by regime change to crash/euphoria)
- **Low volatility:** Every 8 hours (triggered by sideways regime)
- **Emergency:** Immediate (triggered by circuit breaker or major whale movement)

### Why Not Real-Time / Tick-by-Tick

LLM inference takes 5-30 seconds per agent. A full pipeline takes 2-5 minutes. This is fundamentally incompatible with HFT. Our edge is *depth of analysis*, not speed. Every 4 hours is frequent enough for swing/position trading on mid-caps.

### Data Source Priority (if budget is limited)

1. **Must have:** CCXT market data (free), DeFiLlama (free), Fear & Greed (free)
2. **High value:** Dune Analytics (free tier), CryptoPanic (free tier for news)
3. **Nice to have:** Nansen/Arkham (paid, whale tracking), X API (paid for volume)
4. **Can defer:** Governance data, dev activity, token unlocks

---

*This architecture document is a living document. Update as implementation progresses and decisions evolve.*
