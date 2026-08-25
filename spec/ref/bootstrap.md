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
[testing.md](testing.md).

## Scope

The library code does not exist yet. This guide targets the scaffold and
the test suite that will follow; the commands above are forward-looking.