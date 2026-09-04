#!/usr/bin/env bash
# Canonical check set: the full test suite + static checks.
# Single source of truth for local and CI parity — CI runs this exact
# command (see .github/workflows/ci.yml), local developers run it too.
set -euo pipefail

uv run ruff check .
uv run ruff format --check .
uv run mypy unicaptcha
uv run pyright unicaptcha
uv run slotscheck unicaptcha
uv run pytest --cov=unicaptcha --cov-report=term-missing