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
- Live 2Captcha tests live in `tests/test_live_twocaptcha.py`; they solve
  against real workers (credits deducted) and skip when the key is absent:
  `UNICAPTCHA_TWOCAPTCHA_API_KEY=<key> uv run pytest -m integration tests/test_live_twocaptcha.py`.
  Demo sitekeys are public 2Captcha demo pages; the image fixture is a
  generated text captcha under `tests/fixtures/`.
- HTTP is mocked at the transport level (respx; no real API calls); the
  engine exposes an injectable clock/sleep seam for deterministic timing
  tests.
- Examples execute (not just `compile()`): `tests/test_examples.py` runs
  every `examples/` script's `__main__` under respx with canned
  instant-ready 2Captcha responses (no credits, CI-speed), catching API
  misuse like the old `examples/sync/proxy.py` generic-`solve()` bug. A
  companion guard asserts each script is import-safe (executable code only
  under `if __name__ == "__main__":`).
- pytest-asyncio runs in strict mode (`asyncio_mode = "strict"`): every
  async test function needs `@pytest.mark.asyncio`.
- Baseline prerequisite: `tests/` must exist with at least one collectable
  test — pytest exits 4 when `testpaths = ["tests"]` points at a missing
  directory, and 5 when nothing is collected.

### Marker selection

`-m` filters the collected set; CLI `-m` overrides the `addopts` one:

| Command | Runs |
|---|---|
| `uv run pytest` | all tests except `integration` (addopts `-m 'not integration'`) |
| `uv run pytest -m integration` | only `integration`-marked tests; unmarked tests deselected |

They are complements — there is no hybrid state. To run unit tests *plus* a
live file, pass the file explicitly (e.g.
`uv run pytest tests/test_live_twocaptcha.py`) or combine markers; `-m
integration` alone always excludes unmarked tests.

### Live-testing options per provider

Real solves cost credits. Free/low-cost ways to exercise the same wire
surface, per provider research:

- **2Captcha:** `POST https://api.2captcha.com/test` echoes/validates a
  request without solving (wire-contract only). Sandbox mode (account
  setting `/setting#sandbox`) sends tasks to your own dashboard — free, but
  you solve by hand; needs a funded account and does not support reCAPTCHA
  v3 / Turnstile / VK / DataDome.
- **Anti-Captcha:** `POST https://api.anti-captcha.com/test` echoes a JSON
  POST for debugging (wire-contract only); no sandbox.
- **CapMonster Cloud:** no `test` endpoint or sandbox; a $0.1 test balance
  is granted on request to support.
- **Capsolver:** no `test` endpoint or sandbox; `ERROR_CAPTCHA_UNSOLVABLE`
  does not deduct balance (edge-path testing only).

## Static checks

```
uv run ruff check .
uv run ruff format --check .
uv run mypy unicaptcha           # strict ([tool.mypy] strict = true)
uv run pyright unicaptcha        # strict ([tool.pyright] typeCheckingMode = "strict")
uv run slotscheck unicaptcha
```

Mypy/pyright run in strict mode via `pyproject.toml`; the plain `uv run`
invocations pick that up automatically.

Both checkers are scoped to the `unicaptcha` package: mypy via the
explicit `unicaptcha` argument, pyright via `[tool.pyright]
include = ["unicaptcha"]`. The gitignored `var/` tree (third-party source
checkouts for analysis) is deliberately out of scope.

## Acceptance

A task is done when the test suite passes and all static checks are clean.