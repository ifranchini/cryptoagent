# TODO

## In Progress

_(none)_

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

## Ideas / Backlog

- Equity support (Alpaca data provider + broker execution)
- Web dashboard for monitoring
- Ollama support for local model backtesting
- FS-ReasoningAgent fact/subjectivity weighting improvements
- Bull/bear debate mechanism (from TradingAgents architecture)
