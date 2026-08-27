# Task 15: Test scaffold + reference third-party adapter

Status: done

- `tests/` scaffold: conftest, pytest + pytest-asyncio strict mode, respx
  transport mocking, slotscheck, coverage config; integration marker
  (`-m 'not integration'` default).
- Reference third-party adapter **"myservice"** implemented against the
  public API only (ADR-0046); CI-enforced guard that it never imports
  `_internal`.
- Verify all toolchain checks pass (ruff, mypy strict, pyright strict,
  pytest, slotscheck).

References: ADR-0019, ADR-0041, ADR-0046, ADR-0004.

Done:

- `tests/_myservice.py`: complete reference third-party adapter —
  `MyServiceAdapter` (provider "myservice", JSON-family endpoints) with two
  concrete challenge/solution pairs (`MyServiceImageChallenge`/
  `MyServiceRecaptchaV2Challenge`), full contract surface: `build_payload`,
  `parse_submit_response` (errorId → raised public exception with
  `raw_response`; `ready`+solution → **instant fast path**), 4-state
  `parse_task_status`, `parse_balance`, `map_provider_error` (code table),
  **report pairs** bad+good (ADR-0068), per-kind `default_task_config`
  (ADR-0030 extension), trinary `referral`/`base_url`. **Public imports
  only** — never `unicaptcha._internal`.
- `tests/conftest.py`: shared fixtures `myservice_adapter`, `fast_time`,
  `fast_retry` (existing per-file helpers untouched).
- `tests/test_reference_adapter.py` (9 tests): **`_internal`-import guard**
  (AST scan, runs in CI via pytest — satisfies ADR-0046's "CI asserts");
  full-engine solves through a real `Solver` and `AsyncSolver` over respx
  (createTask→getTaskResult→ready); kind-base routing/upcast; instant
  fast path (`submit`→`wait` without polling); aux ops (`get_balance`,
  `get_task_status`, `report_bad_result`, `report_good_result` on
  `/reportIncorrect`+`/reportCorrect`); error mapping to public exception
  classes.
- `pyproject.toml`: `[tool.coverage.run]` (source unicaptcha, omit tests)
  + `[tool.coverage.report] show_missing` — informational only, not forced
  into `addopts` (ADR-0047); `uv run pytest --cov` reports ~84%.
- Verified: 311 tests pass; ruff check/format, mypy strict, pyright strict,
  slotscheck all clean.