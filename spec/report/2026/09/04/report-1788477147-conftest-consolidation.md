## Report on task: conftest fast-config consolidation

### Task (archived from plan.md)

Status: done

`FAST_TIME`/`FAST_RETRY`-style literals are duplicated across
per-provider test files while `conftest.py` already ships `fast_time` /
`fast_retry` fixtures; consolidate (~4 removable copies) and document the
solve-path default in testing.md.

### Done

- The plan's "~4 removable copies" turned out to be **five**: the four
  per-provider test files (`test_capsolver.py`, `test_anticaptcha.py`,
  `test_capmonster.py`, `test_twocaptcha.py`) plus `test_golden_payloads.py`
  each carried a private `_fast_time()`/`_fast_retry()` helper pair
  duplicating the `fast_time`/`fast_retry` fixtures in `tests/conftest.py`
  (verbatim values: `poll_delay` 0, `poll_interval` 0.01, `total_timeout`
  1.0; `max_attempts` 2). All five were consolidated.
- Converted 19 test functions to take the fixtures as function params
  (9 provider facade tests + 10 golden-payload tests) and deleted the 10
  helper functions (~55 net lines removed).
- Removed the dead `FAST_TIME_ARGS` dict in `test_twocaptcha.py`
  (referenced nowhere).
- Deliberately kept `tests/test_engine.py` and `tests/test_client.py`
  module-level `FAST_TIME`/`FAST_RETRY` constants: those use a tighter
  budget (`total_timeout` 0.5 s, `max_attempts` 3) that the engine
  timeout/retry tests depend on, so they are not a duplicate of the
  fixtures.
- Documented the convention in `spec/docs/testing.md`: the fixtures are
  the canonical fast solve-path config; engine/client timing tests keep
  their own constants; slow paths use inline `slow_time` overrides.

### Verification

`uv run ruff check .` / `ruff format --check .` / `mypy unicaptcha` /
`pyright` / `slotscheck unicaptcha` / `uv run pytest` — all pass
(489 passed, 7 integration deselected). No value changes, so no timing
flakiness.

### Spec/ADR amendments

None.

### Future-task notes

- The related "Test-double consolidation (`_fake`/ScriptedAdapter →
  `_myservice`)" plan record remains open; it can follow the same
  consolidation pattern, and the reference `tests/_myservice.py` adapter
  could switch from `BaseAdapter` to `AntiCaptchaCompatAdapterBase`
  (already noted in the adapter-base-rename report).