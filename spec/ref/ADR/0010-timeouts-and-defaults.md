# ADR-0010: Timeouts — total_timeout semantics

**Status:** Accepted (amended 2026-08-23: budget semantics settled as total, name `total_timeout`; per-request timeout confirmed as separate knob)
**Date:** 2026-08-22

## Context

Two timeout layers exist: per-request HTTP timeout (single call) and the
overall solve budget. The budget's scope during submit-phase retries was
contested: (a) total from call start, (b) split submit/poll budgets,
(c) budget starting only after task id obtained. The owner chose total.
Granular submit/solve split is deferred (deferred.md item 10).

## Decision

- **`total_timeout`** (name ratified): the solve budget covers **submit
  attempts + backoff + polling**, starting at the `solve()` call. Exhaustion
  at any phase raises `SolveTimeoutError`.
- Configurable at client level (`SolveConfig`) and per call; resolution via
  the None-merge chain (ADR-0043); concrete defaults per challenge kind in
  the engine's default table (ADR-0030).
- **Per-request HTTP timeout**: separate `HttpClientConfig.timeout` (default
  20 s), independent of the solve budget.
- Async enforcement: the engine runs the solve inside `asyncio.timeout()`;
  the resulting `TimeoutError` is converted to `SolveTimeoutError` at our
  scope boundary only; external cancellations pass through untouched
  (ADR-0016).
- Polling transient-failure tolerance is bounded by the same total budget:
  a lost getTaskResult response costs nothing and is retried inside the
  budget; only budget exhaustion or terminal states end the loop.

## Rationale

- Owner expectation: "when I set a timeout for such a library, I mean the
  total wall-clock of the operation" (submit + solve). The name
  `total_timeout` carries the semantics; `submit_timeout`/`solve_timeout`
  remain open for a later additive split in the same config object.
- One budget = honest arithmetic: `elapsed` and the `failed` event reflect
  exactly what the caller paid for.

## Alternatives considered

- **Budget excludes submit retries** (starts at task id): rejected; total
  wall time becomes weakly bounded; surprises callers with hard outer
  deadlines.
- **Split budgets**: rejected for v1 (two knobs, two interactions with
  retries); deferred as item 10.
- **`timeout` / `deadline` / `max_wait` naming**: rejected in favor of
  `total_timeout`; `deadline` implies a timestamp, `timeout` alone hides
  the total-scope semantics.
