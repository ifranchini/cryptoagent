# TODO

## In Progress

_(none)_

## Planned

### Phase 3: Full Data Richness + Macro Intelligence
- [ ] Real macro data providers (M2 money supply, DXY index, Fed rates via FRED API)
- [ ] Macro regime classifier (risk-on / risk-off)
- [ ] News aggregator (CryptoPanic or Gnews)
- [ ] Protocol fundamentals (token unlocks, governance activity)
- [ ] Insider intelligence (congress trades, whale wallet tracking via Arkham)
- [ ] Add Macro Analyst and Insider Analyst agents (6 analysts total)
- [ ] Redis caching layer for data providers

### Phase 4: Signal Correlation Engine
- [ ] Signal store — log every signal emitted by every analyst
- [ ] Price store — OHLCV at multiple timeframes
- [ ] Correlation engine — compute accuracy by signal x timeframe x regime
- [ ] Signal Correlation Report injected into reasoning context
- [ ] Ablation tests — disable each analyst, measure P&L impact

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

## Ideas / Backlog

- Equity support (Alpaca data provider + broker execution)
- Web dashboard for monitoring
- Ollama support for local model backtesting
- FS-ReasoningAgent fact/subjectivity weighting improvements
- Bull/bear debate mechanism (from TradingAgents architecture)
