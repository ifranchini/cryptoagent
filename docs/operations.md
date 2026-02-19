# Operations Runbook

## Setup

```bash
# Clone and install
git clone <repo-url> && cd cryptoagent
uv sync

# Configure environment
cp .env.example .env
# Edit .env — set at minimum: CA_OPENROUTER_API_KEY (or provider-specific keys)
```

## Run the Agent

```bash
# Single cycle
uv run python -m cryptoagent.cli.main SOL

# Multi-cycle with portfolio carry-forward
uv run python -m cryptoagent.cli.main SOL --cycles 6

# Override models via CLI
uv run python -m cryptoagent.cli.main SOL \
  --brain-model "openrouter/anthropic/claude-sonnet-4" \
  --capital 50000 \
  --cycles 3 -v
```

## Quality Checks

```bash
ruff check cryptoagent/                 # lint
ruff format cryptoagent/                # format
ty check                                # type check
pytest -q                               # test (quick)
uv run pytest -v                        # test (verbose)
```

## Inspect Data

```bash
# View trade history
sqlite3 data/cryptoagent.db "SELECT * FROM trades ORDER BY timestamp DESC LIMIT 10;"

# View reflections
sqlite3 data/cryptoagent.db "SELECT level, timestamp, substr(text, 1, 100) FROM reflections ORDER BY timestamp DESC LIMIT 10;"

# Reset database (start fresh)
rm data/cryptoagent.db
```

## Environment Variables

All config uses `CA_` prefix. Key variables:

| Variable | Required | Purpose |
|----------|----------|---------|
| `CA_OPENROUTER_API_KEY` | Yes (if using OpenRouter) | LLM provider key |
| `CA_BRAIN_MODEL` | No | Model for Brain agent (default: `anthropic/claude-sonnet-4`) |
| `CA_RESEARCH_MODEL` | No | Model for Research agent |
| `CA_SENTIMENT_MODEL` | No | Model for Sentiment agent |
| `CA_TRADER_MODEL` | No | Model for Trader agent |
| `CA_REFLECTION_MODEL` | No | Model for reflection generation |
| `CA_TARGET_TOKEN` | No | Token to trade (default: `SOL`) |
| `CA_INITIAL_CAPITAL` | No | Starting capital (default: `10000.0`) |
| `CA_TWITTER_BEARER_TOKEN` | No | X API v2 for real Twitter data |
| `CA_TWITTER_SCRAPE_URL` | No | Scraping proxy URL for Twitter POC |

See `.env.example` for the full list with defaults.

## Troubleshooting

### LLM API errors (401/403)
1. Verify API key: `echo $CA_OPENROUTER_API_KEY | head -c 20`
2. Check provider status (OpenRouter, Anthropic, etc.)
3. Ensure model string matches provider format (e.g., `openrouter/deepseek/deepseek-chat-v3-0324`)

### No on-chain data (stubs in output)
- DeFiLlama / Solana RPC / Fear & Greed are free APIs — check network connectivity
- The system gracefully degrades to stubs; the pipeline still runs

### No social sentiment data
- Reddit: free, no auth. Check if `reddit.com` is reachable
- Twitter: requires either `CA_TWITTER_BEARER_TOKEN` or `CA_TWITTER_SCRAPE_URL` — shows "not configured" if neither is set

### Database issues
- Default path: `data/cryptoagent.db` (created automatically on first run)
- Delete the file to reset all trade/reflection history
