# Bootstrap

How to set up the local development environment. Run these steps yourself;
the doc only describes them.

## Prerequisites

- Python >= 3.11 (any alive version; 3.13.5 confirmed in use)
- `git`
- `uv` (already installed in the current environment; if missing, see
  "Installing uv" below)

No other system dependencies.

## Installing uv

Primary: the official installer

```
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Fallback: install as a Python package

```
pip install uv
```

## Creating the environment

`uv sync` resolves dependencies from `pyproject.toml`, creates `.venv`, and
installs the runtime dependency (`httpx`) plus the dev group (ruff, mypy,
pyright, pytest, pytest-asyncio, respx, pytest-cov, slotscheck).

```
uv sync
```

Note: `uv.lock` is intentionally **not committed** (stays gitignored).
`uv sync` performs a fresh resolve each time.

## Development loop

All checks (lint, formatting, type checking, tests, slotscheck) run through
`uv run`; the commands and acceptance criteria live in
[testing.md](testing.md). The one-shot command covering everything is
`uv run ./scripts/check.sh` — the same command CI runs, so local and
remote can't drift apart.

## Known toolchain notes

- **Slots dataclass `super()` bug**: `super().__post_init__()` inside a
  `slots=True` dataclass `__post_init__` raises `TypeError`. Never chain a
  base-class `__post_init__` via `super()` in a slots dataclass; call
  shared helpers directly (e.g. `guard_abstract` in `_internal/taxonomy.py`).
- **ruff format ignores `.md`**: `[tool.ruff.format] exclude = ["*.md",
  "*.markdown"]` — ruff 0.11+ would otherwise reformat the code blocks
  inside ADR/README markdown, destroying their alignment.

## Scope

The library code does not exist yet. This guide targets the scaffold and
the test suite that will follow; the commands above are forward-looking.