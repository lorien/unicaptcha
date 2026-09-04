## Report on task: Async clock seam

### Task (archived from plan.md)

Status: done

`Clock.sleep` is sync-only; the async engine sleeps via asyncio directly.
A loop-time injection seam would make async timeout/cadence tests fully
instant (sync tier already has the seam, task 16).

### Done

Investigation showed the async engine enforced budgets via
`asyncio.timeout()` (real event-loop time) at three sites
(`solve`/`wait`/`wait_ref`), so an async sleep seam alone could not make
*timeout* tests instant. Chosen design (owner-approved): injectable async
sleep + clock-deadline budgets.

- `AsyncTaskEngine` gains a `sleep: Callable[[float], Awaitable[None]] | None`
  constructor param (default `asyncio.sleep`); `_sleep` awaits it.
- Replaced the three `asyncio.timeout()` budgets with clock deadlines
  checked between awaits:
  - `solve` computes an absolute `deadline = clock.monotonic() +
    total_timeout` spanning submit+wait and threads the remaining budget
    into `wait` (preserving the previous absolute-budget semantics).
  - `wait`/`_poll` check `clock.monotonic() >= deadline` at the top of each
    poll iteration → emit `RESULT_FAILED` + raise `TaskTimeoutError`;
    cadence/backoff sleeps are bounded by the remaining budget.
  - `wait_ref`/`_poll_ref` return a `PENDING` `TaskStatusResult` on budget
    out.
  - Module docstring updated ("budgets via `asyncio.timeout()`" → clock
    deadlines, mirroring the sync engine).
- Production nuance: the solve budget no longer preempts a single
  in-flight await at the exact boundary; every request is still bounded by
  httpx's per-request timeout (20s default / `NetworkConfig.timeout`), and
  behavior now aligns with the sync engine.
- Tests: new `FakeAsyncSleep(clock)` in `tests/_fake.py` advances a
  `FakeClock` instantly **and yields once** (`await asyncio.sleep(0)`) so
  the event loop is not starved and cancellation stays deliverable — the
  first (non-yielding) version hung the cancellation test. `make_async_engine`
  in `test_engine_timing.py` wires it; `test_async_task_timeout` now uses a
  large fake budget and asserts `clock.sleep_total == 30.0` (was a real
  0.1 s wait); new `test_async_backoff_and_poll_fit_in_budget` mirrors the
  sync tier; the cancellation test's fake budget was raised (10000 s) so it
  stays in-flight when cancelled.

### Verification

`uv run ruff check .` / `ruff format --check .` / `mypy unicaptcha` /
`pyright` / `slotscheck unicaptcha` / `uv run pytest` — all pass
(495 passed, 7 integration deselected; +1 async backoff test).
`tests/test_engine_timing.py` runs in 0.35 s (was seconds of real sleep).

### Spec/ADR amendments

None (ADR-0016 external-cancellation semantics unchanged; internal budget
mechanism changed, documented in the module docstring).

### Future-task notes

- The sync tier still uses a 0.05 s bounded-sleep poll loop in `wait`
  (engine.py:100) — a candidate follow-up to align fully with the async
  deadline pattern, but out of scope here.
- Related deferred tasks remain open: release readiness, CI coverage
  presentation, and the auto-mode feature (ADR-0077).