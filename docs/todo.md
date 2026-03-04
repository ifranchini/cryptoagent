# TODO

## In Progress

_(none)_

## Next Up

### 1. Accumulate signal history + run ablation analysis
- [ ] Run 50+ cycles across different market conditions to populate signal tables
- [ ] Analyze which signals have genuine predictive value at each timeframe
- [ ] Implement weight optimizer — auto-adjust signal weights based on accuracy
- [ ] Implement confluence detection — cross-signal pattern analysis

### 2. Remaining test gaps
- [ ] Unit tests for data providers (mock HTTP responses, verify parsing)
- [ ] Integration test: single pipeline cycle with mocked LLM + data
- [ ] CI: add `pytest -q` to pre-commit or GitHub Actions

## Planned

### Phase 3 (Remaining — deferred, require paid APIs or infra)
- [ ] Token unlocks (Tokenomist API — paid)
- [ ] Insider intelligence: congress trades (Quiver Quantitative — paid)
- [ ] Insider intelligence: whale wallet tracking (Arkham/Nansen — paid)
- [ ] Redis caching layer (deferred — no benefit for CLI single-cycle runs)

### Phase 4: Signal Correlation Engine (Remaining — requires signal history)
- [ ] Ablation tests — disable each analyst, measure P&L impact (needs ~50+ cycles)
- [ ] Weight optimizer — auto-adjust signal weights based on accuracy
- [ ] Confluence detection — cross-signal pattern analysis
- [ ] Lag analysis — identify signal lead times

### Phase 5: Backtesting + Agent Tournament
- [ ] Historical data loader + replay engine
- [ ] Anti-time-travel validation (test on data after model training cutoff)
- [ ] Multi-token, multi-regime backtesting (bull/sideways/bear)
- [ ] Agent Tournament — competing analyst variants scored against market outcomes
- [ ] Hedging check between risk gate and executor
- [ ] Compare vs baselines (buy-and-hold, DCA, MACD)

### Phase 6: Multi-Strategy Parallel Execution
- [ ] Strategy config system + preset profiles (conservative, balanced, aggressive)
- [ ] Parallel strategy runner with isolated capital per strategy
- [ ] Live performance comparison + capital reallocation

### Phase 7: Multi-Token & Multi-Chain
- [ ] Token universe selection logic
- [ ] Parallel graph execution for multiple tokens
- [ ] Portfolio-level cross-position risk management
- [ ] Chain-specific execution routing

### Phase 8: Live Execution
- [ ] CEX executor (CCXT) + DEX executor
- [ ] Circuit breakers and hard limits
- [ ] Notification system (Telegram)
- [ ] VPS deployment
- [ ] Start with $500-1000 max allocation, 30+ day monitor period

## Completed

### Phase 1: Foundation
- [x] 4-agent pipeline (Research + Sentiment → Brain → Trader)
- [x] Real market data via CCXT (SOL/USDT, 12 TA indicators)
- [x] LiteLLM integration (any provider, per-agent model config)
- [x] Paper trading with fee simulation
- [x] LangGraph parallel execution
- [x] Typer CLI with model override flags

### Phase 2: On-Chain Intelligence + Sentiment + Reflection + Risk
- [x] Real on-chain data (DeFiLlama TVL/DEX/fees, Solana RPC TPS/whale activity)
- [x] Real social sentiment (Reddit JSON API, X/Twitter dual-backend)
- [x] Fear & Greed Index (Alternative.me)
- [x] Market regime classifier (bull/bear/sideways + confidence)
- [x] Two-level reflection memory (per-cycle + cross-trial)
- [x] SQLite persistence (trades + reflections)
- [x] Risk Sentinel (daily loss, drawdown, volatility spike checks)
- [x] Multi-cycle CLI (`--cycles N`) with portfolio carry-forward
- [x] Graceful degradation (real data → stub fallback)

### Phase 3: Macro Intelligence + News + Protocol Fundamentals
- [x] FRED API provider (M2 money supply, Fed Funds Rate, Treasury yields, yield curve)
- [x] Macro regime classifier (risk-on / risk-off / neutral)
- [x] CryptoPanic RSS news provider (crypto headlines)
- [x] Macro Analyst agent (5th agent, parallel with Research + Sentiment)
- [x] News integration into Sentiment agent prompt
- [x] Macro report + regime into Brain agent prompt
- [x] Graph wiring (5-agent parallel fan-out)
- [x] CLI updates (--macro-model flag, Macro Report panel)
- [x] Graceful degradation without FRED API key
- [x] Protocol fundamentals via DeFiLlama (protocol TVL, fees, revenue)
- [x] Governance activity via Snapshot GraphQL (active proposals, voting)
- [x] Developer activity via GitHub API (commits, health classification)
- [x] Protocol data integrated into Research Agent prompt
- [x] Brain Agent signal weighting updated with protocol fundamentals guidance

### Phase 4: Signal Correlation Engine
- [x] Signal extractor — extract 17 structured signals from AgentState (5 sources)
- [x] Signal + price persistence — 3 new SQLite tables (signals, price_snapshots, signal_outcomes)
- [x] Signal evaluator — evaluate outcomes at 4h/24h/7d timeframes against actual price
- [x] Signal accuracy report — generate hit-rate report injected into Brain context
- [x] Pipeline integration — pre-pipeline evaluation + post-pipeline extraction in TradingGraph.run()
- [x] Brain Agent updated with signal accuracy guidance in system prompt

### Test Suite + Documentation
- [x] Test dependencies (pytest, pytest-asyncio, pytest-cov, freezegun) in pyproject.toml
- [x] Shared fixtures: in_memory_db, sample_portfolio, sample_market_data, mock_llm
- [x] Unit tests: signal extractor (15 tests), risk sentinel (12), paper trade (12), signal evaluator (8), regime (8)
- [x] Integration tests: persistence layer (10 tests), reflection manager (6 tests)
- [x] 126 tests total, all passing, near-100% coverage on tested modules
- [x] ARCHITECTURE.md rewritten to reflect actual 5-agent pipeline (~250 lines)
- [x] VISION.md created with future plans (debate, multi-strategy, backtesting, live execution)
- [x] CLAUDE.md updated with VISION.md reference

### Web Dashboard
- [x] Next.js 15 app with shadcn/ui, Tailwind CSS, dark theme
- [x] Drizzle ORM schema matching Python's 5 SQLite tables
- [x] Neon serverless PostgreSQL connection
- [x] Overview page (portfolio summary, stats, recent trades/reflections)
- [x] Trades page (full table with detail drawer)
- [x] Signals page (accuracy charts + history table)
- [x] Reflections page (L1/L2 with regime tags)
- [x] AI chat (Vercel AI SDK + OpenRouter, context-aware)
- [x] Python dual-DB support (SQLite + PostgreSQL via CA_DATABASE_URL)
- [x] FastAPI sidecar for pipeline run trigger
- [x] Run trigger button in dashboard UI

### Dashboard E2E Tests
- [x] Playwright setup (config, scripts, .gitignore)
- [x] Navigation tests — sidebar links, active state, cross-page routing (7 tests)
- [x] Overview tests — stat cards, recent trades/reflections, run trigger (7 tests)
- [x] Trades tests — table headers, rows, detail panel click interaction (5 tests)
- [x] Signals tests — accuracy chart, signal history table (4 tests)
- [x] Reflections tests — L1/L2 sections, card content (4 tests)
- [x] Chat tests — empty state, input, suggestions, mocked submit (5 tests)
- [x] 32 E2E tests total, all passing, screenshots captured per test

## Ideas / Backlog

- Equity support (Alpaca data provider + broker execution)
- Ollama support for local model backtesting
- FS-ReasoningAgent fact/subjectivity weighting improvements
- Bull/bear debate mechanism (from TradingAgents architecture)
