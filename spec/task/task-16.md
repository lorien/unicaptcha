# Task 16: Engine tests (injectable clock)

Status: new

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