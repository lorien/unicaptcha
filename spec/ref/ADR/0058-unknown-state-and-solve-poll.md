# ADR-0058: UNKNOWN in the adapter contract; solve-poll fail-fast

**Status:** Accepted (amends the adapter SDK sketch in architecture.md; complements ADR-0050 and ADR-0056; `ParsedTask` typed surface formalized by ADR-0075)
**Date:** 2026-08-23

## Context

ADR-0050 introduced the fourth status value UNKNOWN — "no such task" as
returned data — but the adapter contract still sketches
`parse_task_result(raw) -> ParsedTask # pending|ready|unsolvable`:
three states. The mapping had no home: where does a provider's
TASK_NOT_FOUND / expired-id response land? And no ADR said what
`solve()` does if a mid-solve poll returns not-found for a task the
engine itself submitted.

## Decision

- **`parse_task_result` returns four states**: `pending | ready |
  unsolvable | unknown`. Provider not-found / expired-task / deleted-id
  responses map to **UNKNOWN**.
- **`solve()` mid-poll UNKNOWN fails fast** with `ProviderError`
  (`raw_response` preserved, provider's message carried): a task the
  engine just submitted vanishing is a provider anomaly, not a waiting
  state. Deterministic and consistent with ADR-0011's
  fail-fast-on-ambiguity ethos; the caller may query
  `get_task_result` later to re-examine. It is never silently retried
  and never mislabeled as `SolveTimeoutError`.
- **`get_task_result` returns UNKNOWN as data** (ADR-0050) — the
  legitimate home of the state: reclaim loops after process restarts
  expect it.

## Rationale

- One mapping in one place: the adapter maps provider bytes to states
  exactly once (ADR-0050); the engine's two consumers translate
  differently — solve raises, query answers.
- Mid-poll UNKNOWN cannot be a caller bug (ids originate from the
  engine), so retry/tolerate policies would only burn budget before
  failing anyway; failing at first sight is the honest cheap path.

## Alternatives considered

- **Tolerate UNKNOWN mid-poll, bounded by total_timeout**: rejected;
  converts a provider anomaly into a misleading `SolveTimeoutError`
  after burning the whole budget.
- **Raise `UnknownTaskError`**: rejected; removed from the hierarchy
  by ADR-0050 and impossible to hit on solve() by construction.
- **Map not-found to UNSOLVABLE**: rejected; conflates "solved but
  unsatisfiable" (possibly billed, caller may report bad) with "no
  such task" (different remediation).
