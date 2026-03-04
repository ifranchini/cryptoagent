# CryptoAgent: Long-Term Vision

> Future architecture plans and research-backed design ideas. These are NOT implemented yet.
> See [ARCHITECTURE.md](ARCHITECTURE.md) for what's actually built today.
> See [crypto-trading-agents-research.md](crypto-trading-agents-research.md) for the full landscape analysis.
> Last updated: March 2026

---

## Table of Contents

1. [Full LangGraph Flow (Aspirational)](#1-full-langgraph-flow-aspirational)
2. [Multi-Strategy Parallel Execution](#2-multi-strategy-parallel-execution)
3. [Risk Profile Configurations](#3-risk-profile-configurations)
4. [Competitive Agent Scoring](#4-competitive-agent-scoring-from-contesttrade)
5. [Hedging Layer](#5-hedging-layer-from-hedgeagents)
6. [Backtesting Harness](#6-backtesting-harness)
7. [Decoupled Real-Time Risk Sentinel](#7-decoupled-real-time-risk-sentinel)
8. [Insider Intelligence Layer](#8-insider-intelligence-layer)
9. [Bull/Bear Debate Mechanism](#9-bullbear-debate-mechanism)
10. [Three-Perspective Risk Gate](#10-three-perspective-risk-gate)
11. [Live Execution Engine](#11-live-execution-engine)

---

## 1. Full LangGraph Flow (Aspirational)

The current system uses a 5-agent parallel pipeline. The full vision expands to a 13-node graph with debate and multi-perspective risk:

```
START → All 6 analysts run concurrently (fan-out)
  ├── On-Chain Analyst ──┐
  ├── Technical Analyst ──┤
  ├── Sentiment Analyst ──┤ converge
  ├── Protocol Analyst ──┤
  ├── Macro Analyst ──────┤
  └── Insider Analyst ────┘
          │
    Regime Detector + Reflection Analyst (parallel)
          │
    Bull Researcher ◄──► Bear Researcher (debate rounds)
          │
    Research Manager (summarize debate)
          │
    Trader Agent (synthesize all inputs)
          │
    Risk Gate: Aggressive / Neutral / Conservative + Judge
          │
    Executor (CEX/DEX/Paper)
          │
    Post-Execution Reflection + Memory Update
```

Key additions over current system:
- **On-Chain Analyst** and **Protocol Analyst** as separate agents (currently data feeds into Research)
- **Insider Analyst** for congress trades, whale wallets, VC movements
- **Bull/Bear debate** mechanism from TradingAgents
- **Three-perspective risk gate** (aggressive/neutral/conservative + judge)
- **Executor node** with CEX/DEX routing

---

## 2. Multi-Strategy Parallel Execution

Run multiple strategies simultaneously with different risk profiles and timeframes:

```
┌──────────────────────────────────────────────────────┐
│                 STRATEGY ORCHESTRATOR                  │
│                                                        │
│  ┌──────────────────┐  ┌──────────────────┐           │
│  │ Conservative     │  │ Balanced Daily   │           │
│  │ Weekly (40%)     │  │ (30%)            │           │
│  │ BTC,ETH,SOL     │  │ Mid-caps         │           │
│  │ Full pipeline    │  │ Full pipeline    │           │
│  └──────────────────┘  └──────────────────┘           │
│                                                        │
│  ┌──────────────────┐  ┌──────────────────┐           │
│  │ Aggressive 4h   │  │ Moonshot (10%)   │           │
│  │ (20%)           │  │ Low-cap gems     │           │
│  │ Trending alts   │  │ Full pipeline    │           │
│  │ Full pipeline   │  │                  │           │
│  └──────────────────┘  └──────────────────┘           │
│                                                        │
│  ┌──────────────────────────────────────────┐         │
│  │ STRATEGY COMPARATOR + CAPITAL ALLOCATOR  │         │
│  │ Quarterly rebalance based on performance │         │
│  └──────────────────────────────────────────┘         │
└──────────────────────────────────────────────────────┘
```

Each strategy runs its own full agent pipeline with isolated capital. A Strategy Comparator tracks Sharpe ratio, return, drawdown, win rate per strategy. A Capital Allocator rebalances quarterly toward best performers.

The allocation follows a barbell strategy:
- **Safe side (70%)**: Conservative weekly + balanced daily
- **Risk side (30%)**: Aggressive 4h + moonshot bets

---

## 3. Risk Profile Configurations

Pre-built strategy presets with different risk parameters:

| Preset | Frequency | Max Position | Max Exposure | Stop Loss | Target Return |
|--------|-----------|-------------|-------------|-----------|--------------|
| Conservative Weekly | Weekly | 15% | 50% | 8% | 20%/yr |
| Balanced Daily | Daily | 10% | 70% | 5% | 40%/yr |
| Aggressive 4h | 4 hours | 15% | 80% | 3% | 100%/yr |
| Moonshot | Daily | 20% | 100% | 50% | 10x |
| Macro Monthly | Monthly | 25% | 60% | 15% | 30%/yr |

Each preset adjusts signal weights based on correlation engine data:
- Weekly strategies weight macro/whale signals higher
- 4h strategies weight funding rates/RSI higher
- Moonshot strategies weight on-chain accumulation + narrative momentum

---

## 4. Competitive Agent Scoring (from ContestTrade)

Run multiple competing variants per analyst role and score them against real market outcomes:

```python
class AgentTournament:
    """Run 2-3 variants per analyst role, score against market."""

    # Example: On-Chain Analyst variants
    # Variant A: CryptoTrade-style (tx stats focus)
    # Variant B: Whale-movement focus
    # Variant C: Exchange flow focus

    # Score each variant's predictions against actual price movements
    # Select output from top-performing variant
    # Update scores after price action is known
```

From ContestTrade (arXiv: 2508.00554): continuous scoring and ranking ensures only the best-performing agents' outputs are adopted. This creates a Darwinian selection mechanism for analyst quality.

---

## 5. Hedging Layer (from HedgeAgents)

After Risk Gate approves but before execution, a hedging check runs:

- If total crypto exposure > 60%, suggest stablecoin hedge
- If concentrated in single sector > 30%, suggest diversification
- In bear/crash regime, reduce to minimum exposure
- For moonshot positions, enforce barbell allocation caps

HedgeAgents (WWW '25) showed 70% annualized return with explicit hedging that prevents catastrophic drawdowns during rapid declines.

---

## 6. Backtesting Harness

The hardest unsolved problem. Key constraints from academic research:

**DeepFund (NeurIPS 2025)**: Even top LLMs lose money in real-time — historical backtesting inflates results via "time travel" (LLMs using future knowledge from training data).

**FINSABER (KDD 2026)**: LLM advantages disappear under broad, long-term evaluation. LLM strategies are too conservative in bull markets and too aggressive in bear markets.

Our backtesting must:
1. Use data AFTER model's training cutoff for final validation
2. Test across 10+ tokens and multiple regimes (not just cherry-picked periods)
3. Run multiple trials (LLM responses are non-deterministic)
4. Use cheap models (DeepSeek, Ollama) for iteration ($10-40 per backtest run)
5. Track per-regime performance separately

```
backtesting/
├── historical_data.py       # Load historical OHLCV + on-chain + sentiment
├── replay_engine.py         # Feed historical data through agent pipeline
├── mock_execution.py        # Simulated fills with historical slippage
├── metrics.py               # Sharpe, max drawdown, win rate, profit factor
└── report_generator.py      # HTML/Markdown performance reports
```

---

## 7. Decoupled Real-Time Risk Sentinel

From WebCryptoAgent (arXiv: 2601.04687): separate strategic reasoning (minutes) from real-time risk monitoring (seconds).

The current Risk Sentinel runs synchronously in the pipeline. The vision is a truly decoupled sentinel running in a separate process/thread:

```
SLOW PATH (minutes):              FAST PATH (seconds):
┌─────────────────────┐           ┌─────────────────────────┐
│ LangGraph Pipeline  │           │ RISK SENTINEL           │
│ Analysts → Brain →  │           │ Runs independently      │
│ Trader              │  OVERRIDE │ Monitors:               │
│                     │ ◄─────── │  - Price feeds (1s)     │
│ ┌─────────────────┐ │           │  - Flash crash detect   │
│ │ Executor        │ │           │  - Stablecoin depeg     │
│ │ (can be halted) │ │           │  - Volume anomalies     │
│ └─────────────────┘ │           │ Can halt execution      │
└─────────────────────┘           └─────────────────────────┘
```

---

## 8. Insider Intelligence Layer

New data providers for smart money tracking:

| Signal | Source | Access |
|--------|--------|--------|
| US Congress trades | Quiver Quantitative API | Paid |
| Named whale wallets | Arkham Intelligence | API (free + paid) |
| VC fund wallets | Arkham + Nansen | Paid |
| Exchange reserves | CryptoQuant / Glassnode | Paid |
| Team/founder wallets | Manual curation + Arkham | Mixed |

These feed into a dedicated Insider Analyst agent that reports:
- Whale consensus: accumulating / distributing / neutral
- Congress signal: buying / selling / no activity
- VC signal: deploying / harvesting / holding
- Team risk: founder selling / vesting unlocks claimed

---

## 9. Bull/Bear Debate Mechanism

From TradingAgents: structured multi-round debate before trading decisions.

**Bull Researcher** builds the strongest case for entering/holding a position. **Bear Researcher** builds the strongest case against. They debate for configurable rounds (default: 2), each responding to the other's arguments.

This reduces single-agent bias and hallucination. Each researcher maintains persistent memory of past arguments and their outcomes.

---

## 10. Three-Perspective Risk Gate

From TradingAgents: three risk managers (aggressive/neutral/conservative) evaluate proposed trades, then a Risk Judge makes the final call:

- **APPROVE**: Execute as proposed
- **MODIFY**: Execute with adjusted size/stops
- **REJECT**: Do not execute

Crypto-specific risk checks to add:
- Portfolio concentration limits (no > 25% in single asset)
- Correlation risk (avoid over-exposure to same sector)
- Liquidity check (reject if estimated slippage > 2%)
- Smart contract risk flag (is protocol audited?)
- Market regime override (reduce all sizes in crash regime)

---

## 11. Live Execution Engine

Graduate from paper trading to real execution:

```
execution/
├── router.py              # Route orders to correct venue
├── cex_executor.py        # CCXT-based CEX execution (Binance, Bybit, OKX)
├── dex_executor.py        # On-chain DEX (1inch/Uniswap on ETH, Jupiter on Solana)
├── order_manager.py       # Track open orders, fills, cancellations
├── slippage_model.py      # Estimate slippage before execution
└── anti_mev.py            # Private RPCs (Flashbots Protect, Jito bundles)
```

Order types: MARKET, LIMIT, STOP_LOSS, TAKE_PROFIT, trailing stop.

Prerequisites before live deployment:
- 30+ days of profitable paper trading
- Backtesting validation on post-training-cutoff data
- Circuit breakers and hard limits verified
- Start with $500-1000 max allocation

---

*This vision document captures research-backed ideas from TradingAgents, CryptoTrade, HedgeAgents, FS-ReasoningAgent, ContestTrade, WebCryptoAgent, DeepFund, FINSABER, and others. See [crypto-trading-agents-research.md](crypto-trading-agents-research.md) for full citations and analysis.*
