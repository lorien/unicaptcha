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

## Done

- Owner decisions: (Q1) two engine classes — `TaskEngine` (sync, real
  blocking) + `AsyncTaskEngine` (async-native) sharing pure helpers;
  (Q2) the client resolves routing and passes the adapter per call —
  engines are registry-free; (Q3) adapters own the poll/balance request
  bodies — concrete `build_task_status`/`build_balance` JSON-family
  defaults added to `BaseAdapter` (task-7 contract amendment), engine is
  body-agnostic (future legacy protocols override); (Q4) three commits.

- `_internal/` additions: `backoff.py` (full jitter), `clock.py`
  (injectable monotonic/wallclock seam; task 16 injects fakes),
  `retry.py` (submit-phase classification; pre-send vs after-send via
  the chained httpx cause), `errors.py` (ErrorKind -> exception, the
  shared 1:1 table), `defaults.py` (ADR-0030 kind table + generic
  fallback + resolve_time/resolve_retry over the None-merge chain;
  concrete ResolvedTime/ResolvedRetry), `registry.py`
  (AbandonedTaskRegistry).

- Core (commit 1): submit with the ADR-0011/0059 retry loop
  (pre-send + 500/503 + 429 retryable -> RateLimitError on exhaustion;
  busy payloads -> ServiceBusyError; 502/504/read-timeout fail-fast
  NetworkError; non-200 provider bodies via adapter.map_provider_error),
  poll loop (fresh-ticket poll_delay rule, NO_SOLUTION ->
  NoSolutionError, UNKNOWN -> ProviderError fail-fast, READY ->
  TaskResult with cost presence-check and created_at/elapsed),
  instant-answer fast path (ADR-0075), sync deadline budgets vs async
  `asyncio.timeout()` -> TaskTimeoutError at the boundary;
  CancelledError passes through untouched (ADR-0016). Events per
  ADR-0018. `TaskTicket` gained `time` (resolved timing carried from
  submit; wait derives budget/cadence — ADR-0030 amendment); adapter
  `base_url` promoted to a public attribute.

- Aux (commit 2): shared `_post_retried` (parse callback; aux ops are
  eventless), `wait_ref` (answers, PENDING on budget-out, no poll
  delay, generic timing fallback), `get_task_status` (single-shot,
  answers), `get_balance` (USD Decimal), `report_bad/good_result`
  (bool; default-unsupported raises UnsupportedChallengeError).

- Registry + lifecycle (commit 3): bounded thread-safe registry (cap
  1000/None, WARNING per eviction, survives close); add at submit
  acceptance, remove on delivery and same-client terminal status
  queries; sync `close()` idempotent — shutdown event wakes blocked
  solves -> ClientClosedError with the ref staying registered; async
  `aclose()` idempotent (client cancels in-flight tasks);
  `get_abandoned_tasks()` readable after close.

- Tests: 203 passing (core happy paths, retry/exhaustion/fail-fast,
  provider error mapping, terminal states, timeouts, cancellation
  pass-through, aux ops, registry lifecycle, close semantics; both
  tiers). Full deterministic timing suite is task 16 (injectable clock).
- Full suite green (ruff, mypy strict, pyright strict, slotscheck).
  No hard-coded credentials.