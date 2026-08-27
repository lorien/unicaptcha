# Task 16: Engine tests (injectable clock)

Status: done

Deterministic, instant engine tests via the injectable clock/sleep seam:

- Total-budget semantics: submit+backoff+polling inside `total_timeout`;
  `TaskTimeoutError` on exhaustion; per-kind default table rows
  (ADR-0030) honored.
- Retry/backoff: full-jitter backoff math, attempt caps, 429 → retry →
  `RateLimitError`, busy payloads → `ServiceBusyError`, fail-fast
  502/504.
- Poll cadence: `poll_delay` first-useful-poll, `poll_interval`;
  fresh-ticket vs stale-ticket wait behavior; poll-delay skip in
  wait_ref/get_task_status.
- Cancellation (async) propagates eventless; sync close shutdown flag;
  abandoned-task registry bookkeeping; two-phase submit/wait and the
  instant-answer fast path.

References: ADR-0010, ADR-0011, ADR-0016, ADR-0030, ADR-0033, ADR-0038,
ADR-0059, ADR-0067, ADR-0075.

Done:

- Seam completion (`_internal/clock.py`): `Clock` protocol gains sync
  `sleep(seconds)`; `RealClock.sleep` = `time.sleep`. The async engine
  keeps `asyncio.sleep` for real waiting (blocking the loop with
  `time.sleep` was rejected after profiling).
- Sync `TaskEngine._sleep` reworked: sleeps through the injectable clock
  in ≤0.05 s slices, re-checking the shutdown flag each slice — preserves
  ADR-0033 close-wakeup (latency ≤ one slice) while a fake clock advances
  instantly. Async `_sleep` unchanged (`asyncio.sleep`).
- `tests/_fake.py::FakeClock`: instant monotonic/wallclock + `sleep` that
  advances fake time (records per-call + total); `advance()` for stale
  tickets.
- `tests/test_engine_timing.py` (20 tests, both tiers): full-jitter
  backoff bounds/cap; total-budget fit + exhaustion; per-kind default rows
  (image 30/2/5, recaptcha 120/5/15, funcaptcha/geetest 180/3/10,
  turnstile 120/3/5 — total/interval/delay); attempt cap 3, 429 → retry →
  `RateLimitError`, busy → `ServiceBusyError`, 502/504 fail-fast;
  `poll_delay` on fresh tickets, skipped on stale tickets and in
  `wait_ref`; `poll_interval` cadence; async cancellation eventless;
  async timeout; two-phase submit/wait; instant-answer fast path;
  use-after-close raises `ClientClosedError`.
- Verified: 331 tests pass; ruff check/format, mypy strict, pyright
  strict, slotscheck all clean. No hard-coded credentials.