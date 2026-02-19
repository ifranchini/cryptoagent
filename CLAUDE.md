# Global Development Standards

Global instructions for all projects. Project-specific CLAUDE.md files override these defaults.

- Prefer Exa AI (`mcp__exa__web_search_exa`) over `WebSearch` for all web searches
- Use skills proactively when they match the task — suggest relevant ones, don't block on them

## Philosophy

- **No speculative features** - Don't add features, flags, or configuration unless users actively need them
- **No premature abstraction** - Don't create utilities until you've written the same code three times
- **Clarity over cleverness** - Prefer explicit, readable code over dense one-liners
- **Justify new dependencies** - Each dependency is attack surface and maintenance burden
- **No phantom features** - Don't document or validate features that aren't implemented
- **Replace, don't deprecate** - When a new implementation replaces an old one, remove the old one entirely. No backward-compatible shims, dual config formats, or migration paths. Proactively flag dead code — it adds maintenance burden and misleads both developers and LLMs.
- **Verify at every level** - Set up automated guardrails (linters, type checkers, pre-commit hooks, tests) as the first step, not an afterthought. Prefer structure-aware tools (ast-grep, LSPs, compilers) over text pattern matching. Review your own output critically. Every layer catches what the others miss.
- **Bias toward action** - Decide and move for anything easily reversed; state your assumption so the reasoning is visible. Ask before committing to interfaces, data models, architecture, or destructive/write operations on external services.
- **Finish the job** - Don't stop at the minimum that technically satisfies the request. Handle the edge cases you can see. Clean up what you touched. If something is broken adjacent to your change, flag it. But don't invent new scope — there's a difference between thoroughness and gold-plating.
- **Agent-native by default** - Design so agents can achieve any outcome users can. Tools are atomic primitives; features are outcomes described in prompts. Prefer file-based state for transparency and portability. When adding UI capability, ask: can an agent achieve this outcome too?

## Code Quality

### Hard limits

1. ≤100 lines/function, cyclomatic complexity ≤8
2. ≤5 positional params
3. 100-char line length
4. Absolute imports only — no relative (`..`) paths
5. Google-style docstrings on non-trivial public APIs

### Zero warnings policy

Fix every warning from every tool — linters, type checkers, compilers, tests. If a warning truly can't be fixed, add an inline ignore with a justification comment. Never leave warnings unaddressed; a clean output is the baseline, not the goal.

### Comments

Code should be self-documenting. No commented-out code—delete it. If you need a comment to explain WHAT the code does, refactor the code instead.

### Error handling

- Fail fast with clear, actionable messages
- Never swallow exceptions silently
- Include context (what operation, what input, suggested fix)

### Reviewing code

Evaluate in order: architecture → code quality → tests → performance. Before reviewing, sync to latest remote (`git fetch origin`).

For each issue: describe concretely with file:line references, present options with tradeoffs when the fix isn't obvious, recommend one, and ask before proceeding.

### Testing

**Test behavior, not implementation.** Tests should verify what code does, not how. If a refactor breaks your tests but not your code, the tests were wrong.

**Test edges and errors, not just the happy path.** Empty inputs, boundaries, malformed data, missing files, network failures — bugs live in edges. Every error path the code handles should have a test that triggers it.

**Mock boundaries, not logic.** Only mock things that are slow (network, filesystem), non-deterministic (time, randomness), or external services you don't control.

**Verify tests catch failures.** Break the code, confirm the test fails, then fix. Use mutation testing (`cargo-mutants`, `mutmut`) to verify systematically. Use property-based testing (`proptest`, `hypothesis`) for parsers, serialization, and algorithms.

## Development

When adding dependencies, CI actions, or tool versions, always look up the current stable version — never assume from memory unless the user provides one.

### CLI tools

| tool | replaces | usage |
|------|----------|-------|
| `rg` (ripgrep) | grep | `rg "pattern"` - 10x faster regex search |
| `fd` | find | `fd "*.py"` - fast file finder |
| `ast-grep` | - | `ast-grep --pattern '$FUNC($$$)' --lang py` - AST-based code search |
| `shellcheck` | - | `shellcheck script.sh` - shell script linter |
| `shfmt` | - | `shfmt -i 2 -w script.sh` - shell formatter |
| `actionlint` | - | `actionlint .github/workflows/` - GitHub Actions linter |
| `zizmor` | - | `zizmor .github/workflows/` - Actions security audit |
| `prek` | pre-commit | `prek run` - fast git hooks (Rust, no Python) |
| `wt` | git worktree | `wt switch branch` - manage parallel worktrees |
| `trash` | rm | `trash file` - moves to macOS Trash (recoverable). **Never use `rm -rf`** |

Prefer `ast-grep` over ripgrep when searching for code structure (function calls, class definitions, imports, pattern matching across arguments). Use ripgrep for literal strings and log messages.

### Python

**Runtime:** 3.13 with `uv venv`

| purpose | tool |
|---------|------|
| deps & venv | `uv` |
| lint & format | `ruff check` · `ruff format` |
| static types | `ty check` |
| tests | `pytest -q` |

**Always use uv, ruff, and ty** over pip/poetry, black/pylint/flake8, and mypy/pyright — they're faster and stricter. Configure `ty` strictness via `[tool.ty.rules]` in pyproject.toml. Use `uv_build` for pure Python, `hatchling` for extensions.

Tests in `tests/` directory mirroring package structure. Supply chain: `pip-audit` before deploying, pin exact versions (`==` not `>=`), verify hashes with `uv pip install --require-hashes`.

# CryptoAgent

Multi-agent LLM trading system. 4 agents (Research, Sentiment, Brain, Trader) orchestrated via LangGraph, with LiteLLM for model routing, CCXT for market data, and real on-chain/social data sources. Paper trading only — no live execution yet.

## Quick Reference

```bash
# Setup
uv sync

# Run single cycle
uv run python -m cryptoagent.cli.main SOL

# Run multi-cycle
uv run python -m cryptoagent.cli.main SOL --cycles 6

# Quality
ruff check cryptoagent/                 # lint
ruff format cryptoagent/                # format
ty check                                # type check
pytest -q                               # test
```

### Always allowed (run without asking)

- **Git read ops**: `git status`, `git log`, `git branch`, `git diff`, `git remote -v`
- **File reads**: reading any file within the cryptoagent project
- **Quality tools**: `ruff check`, `ruff format`, `ty check`, `pytest`
- **Running the agent**: `uv run python -m cryptoagent.cli.main`

### Ask user first

- **Destructive data ops**: deleting `data/cryptoagent.db`, clearing trade/reflection history
- **Git write ops**: `git push --force`, rebasing, resetting branches
- **Config edits**: modifying `.env` files (API keys, tokens)
- **Dependency changes**: adding/removing packages in `pyproject.toml`

## Workflow

**Before committing:**
1. Re-read your changes for unnecessary complexity, redundant code, and unclear naming
2. Run relevant tests — not the full suite
3. Run linters and type checker — fix everything before committing

**Git Conventions:**
- Imperative mood, ≤72 char subject line, one logical change per commit
- Commit format: Conventional Commits (feat:, fix:, docs:, etc.)
- Never commit secrets, API keys, or credentials — use `.env` files (gitignored)

## Architecture

```
DATA LAYER (CCXT + DeFiLlama + Solana RPC + Reddit + X/Twitter + Fear & Greed)
        │
  ┌─────┴─────┐
  ▼           ▼
Research   Sentiment     ← cheap/fast LLMs (parallel)
  │           │
  └─────┬─────┘
        ▼
      Brain              ← best reasoning LLM (+ regime, on-chain, reflections)
        │
        ▼
      Trader             ← fast LLM → paper execution

Pre-pipeline:  Risk Sentinel pre-check, regime classification, reflection loading
Post-pipeline: Trade logging (SQLite), Level 1/2 reflection generation
```

See @docs/ARCHITECTURE.md for the full long-term vision.

## Key Paths

| Location | Purpose |
|----------|---------|
| `cryptoagent/config.py` | Pydantic settings (`CA_` env prefix) |
| `cryptoagent/agents/` | 4 agent implementations |
| `cryptoagent/dataflows/` | Data providers (market, onchain, social, regime) |
| `cryptoagent/graph/builder.py` | LangGraph wiring + pre/post pipeline |
| `cryptoagent/persistence/` | SQLite trade + reflection storage |
| `cryptoagent/reflection/manager.py` | Two-level reflection system |
| `cryptoagent/risk/sentinel.py` | Risk threshold checks |
| `cryptoagent/cli/main.py` | Typer CLI entry point |
| `.env` / `.env.example` | API keys and model config |
| `data/cryptoagent.db` | SQLite database (gitignored) |

## Task Tracking

**ALWAYS update `docs/todo.md`** when working on tasks:
- Move items to "In Progress" when starting work
- Move items to "Completed" when done
- Add new items to "Planned" or "Ideas / Backlog" when discovered

## Code Style

- **ruff**: lint + format, line-length 100, Python 3.13
- **ty**: strict type checking via `[tool.ty.rules]` in pyproject.toml
- **uv**: package management (not pip/poetry)
- **pytest-asyncio**: `asyncio_mode = "auto"`

## Branch Strategy

| Branch | Purpose |
|--------|---------|
| `main` | Primary development branch |

## Documentation

- @docs/ARCHITECTURE.md — long-term vision and full system design
- @docs/crypto-trading-agents-research.md — landscape research and framework analysis
- @docs/operations.md — runbook for common dev tasks
- @docs/todo.md — current tasks and backlog
