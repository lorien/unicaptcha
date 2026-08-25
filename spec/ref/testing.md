# Testing

How to run the project's test suite and static checks. All commands run
through `uv run` inside the project's virtualenv (see
[bootstrap.md](bootstrap.md) for environment setup).

## Test suite

```
uv run pytest                    # tests; integration tests deselected by default
```

- Integration tests (real provider APIs, API keys via environment) are
  gated by the `integration` marker and deselected by default:
  `uv run pytest -m integration`.
- HTTP is mocked at the transport level (respx; no real API calls); the
  engine exposes an injectable clock/sleep seam for deterministic timing
  tests.

## Static checks

```
uv run ruff check .
uv run ruff format --check .
uv run mypy unicaptcha           # strict ([tool.mypy] strict = true)
uv run pyright                   # strict ([tool.pyright] typeCheckingMode = "strict")
uv run slotscheck unicaptcha
```

Mypy/pyright run in strict mode via `pyproject.toml`; the plain `uv run`
invocations pick that up automatically.

## Acceptance

A task is done when the test suite passes and all static checks are clean.