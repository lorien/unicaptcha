# Task 9: TaskEngine

Status: new

Implement the internal `_internal` engine (submit → poll → result):

- Submit phase: build payload, POST createTask, retry policy — full
  jitter backoff (base 1 s, cap 30 s, max 3 attempts); 429 + provider
  payloads retryable → `RateLimitError`; busy/no-slot payloads →
  `ServiceBusyError`; read-timeout/reset/502/504 fail fast `NetworkError`.
- Poll phase: initial `poll_delay`, interval cadence, per-kind default
  table (ADR-0030 incl. FunCaptcha/GeeTest 10/3/180, Turnstile 5/3/120);
  NO_SOLUTION → `NoSolutionError`; UNKNOWN → `ProviderError` fail fast;
  solved-but-empty → `EmptySolutionError`.
- `total_timeout` budget via `asyncio.timeout()` (async), converted at
  scope boundary; `TaskTimeoutError`; external cancellation passes
  through (eventless).
- Two-phase: `submit()`/`wait()`/`wait_ref()` with ticket freshness
  rule, instant-answer fast path; aux ops (`get_balance`,
  `get_task_status`, `report_*_result`) share the retry policy.
- Events per kind; abandoned-task registry (bounded, survives close);
  lifecycle: close/aclose idempotent, sync shutdown flag, registry
  survives close.
- Injectable clock/sleep seam for deterministic tests.

References: ADR-0010, ADR-0011, ADR-0016, ADR-0018, ADR-0030, ADR-0033,
ADR-0038, ADR-0050, ADR-0058, ADR-0059, ADR-0060, ADR-0067, ADR-0075,
ADR-0071 (endpoints).