# ADR-0019: Toolchain

**Status:** Accepted (amended: slotscheck added; pre-commit/vulture/freezegun/basedpyright rejected)
**Date:** 2026-08-22

## Context

The project needs build tooling, linting, typing gates, and a test stack,
chosen before implementation begins so configuration is written once.

## Decision

| Concern | Choice |
|---|---|
| Dependency/build management | uv + pyproject.toml; hatchling backend |
| Lint + format | ruff (E, W, F, I, B, UP, SIM, RUF; target py311; 88 cols; no ANN) |
| Type checking | mypy strict + pyright strict, both in CI |
| Tests | pytest + pytest-asyncio (strict mode) + respx (HTTP transport mocking) |
| Coverage | pytest-cov, informational only |
| Extras audit | slotscheck |
| Dependency groups | PEP 735 `[dependency-groups]` dev group holding all dev tools |

- Integration suite (real APIs, keys via environment) marked `integration`,
  deselected by default (`addopts = "-m 'not integration'"`).
- No optional dependency extras in v1 (no optional features).
- Runtime dependencies: `httpx>=0.27` only.

Rejected additions, with reasons:

- **pre-commit**: git-hook lifecycle for tooling already enforced in CI;
  also no git repo exists yet at design time.
- **vulture**: dead-code detection, false-positive-prone against dynamic
  dispatch and public exports.
- **freezegun/time-machine**: superseded by the engine's injectable
  clock/sleep seam (deterministic tests without global patching).
- **basedpyright**: pyright explicitly chosen; fork adds no needed value.
- **ANN ruff rules**: annotations already enforced by two strict type
  checkers; lint duplication is noise.

## Rationale

- Single-tool-per-concern (ruff covers lint+format; uv covers env+build);
  modern, fast, minimal configuration surface.
- respx matches the httpx-only dependency story and tests the actual
  transport boundary without real networks.
- slotscheck is cheap and aligns with frozen-dataclass + memory-conscious
  model design.

## Alternatives considered

- **Poetry / Hatch pipeline / setuptools**: rejected in favor of uv +
  hatchling.
- **black + flake8 + isort**: rejected; ruff subsumes all three.
- **aiohttp + requests split**: rejected; httpx serves both execution
  models with one API.
