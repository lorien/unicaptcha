## Report on task: Example verification — execute, not just compile

Closed the plan.md record of the same name. `tests/test_examples.py` only
`compile()`d examples, which missed a facade-attribute misuse in
`examples/sync/proxy.py` (generic `solve()` on a per-kind facade) that the
2026-08-28 live smoke caught.

### Done

- All 30 examples (15 sync + 15 async) are now import-safe: executable
  code lives under `if __name__ == "__main__":` guards. Sync examples
  wrap the api_key check + flow in the guard; async examples wrap the
  trailing `asyncio.run(main())`. Direct execution
  (`python examples/sync/recaptcha_v2.py`) is unchanged.
- `tests/test_examples.py` now executes every example against a
  respx-mocked 2Captcha transport (no credits, CI-speed):
  - `test_examples_execute` — 28 happy-path runs; `createTask` returns a
    per-file instant-ready solution (fast path, no polling sleeps) with
    `getTaskResult`/`getBalance`/`reportCorrect`/`reportIncorrect` mocked;
    asserts completion and a per-file stdout marker.
  - `test_error_example_executes` — sync/async `errors.py` run with a
    submit-time `ERROR_ZERO_BALANCE` (avoids the poll_delay/retry path),
    asserting `SystemExit(1)` and the `kind=` output.
  - `test_examples_are_import_safe` — `exec()`-level guard that any new
    example keeps executable code under `__main__`.
  - Solution shapes mirror `TwoCaptchaAdapter._solution_from` dispatch
    (image/text, v2, v3, token-only, GeeTest v3/v4).
- Verified the regression is caught: temporarily restoring the old
  `client.solve(...)` misuse in `proxy.py` fails
  `test_examples_execute[sync/proxy.py]` with the same `AttributeError`.
- Docs: `spec/docs/testing.md` notes the example-execution coverage;
  CHANGELOG Unreleased **Fixed** entry.

### Verification

`uv run ruff check .` / `ruff format --check` / `mypy unicaptcha` /
`pyright` / `slotscheck unicaptcha` / `uv run pytest` — all pass
(487 passed, 7 integration deselected).

### Future-task notes

- The related plan record "Example demo values: geetest_v3 dynamic
  challenge; funcaptcha annotation" stays open; the execute tests run
  those examples with mocked responses, so demo-value staleness is
  orthogonal (still a live-run concern).
- "README snippet verification" could reuse the same respx-mock harness
  for README fenced blocks.