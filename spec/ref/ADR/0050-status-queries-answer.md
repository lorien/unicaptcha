# ADR-0050: Status queries answer, operations raise

**Status:** Accepted (supersedes the UnknownTaskError decision; TaskStatus surface per ADR-0056)
**Date:** 2026-08-23

## Context

`get_task_result()` originally inherited exception semantics from
`solve()`: UNSOLVABLE would raise `UnsolvableCaptchaError`, unknown ids
would raise `UnknownTaskError` (settled during malformed-response
mapping). But the method's primary caller is a reclaim loop over the
abandoned registry — every iteration would need try/except armor for
outcomes that, from a query's perspective, are perfectly good answers.

## Decision

- **Principle**: status queries answer; operations raise.
- `TaskStatus.status` has **four values**: `PENDING`, `READY`,
  `UNSOLVABLE`, `UNKNOWN`. Provider-side outcomes are always returned
  values on `get_task_result`.
- Exceptions on the query are reserved for caller-side faults:
  provider-mismatch `TypeError` (ADR-0045), `ClientClosedError`,
  `NetworkError` (transport), `InvalidConfigError`.
- **`UnknownTaskError` is removed** from the hierarchy; `ErrorKind` loses
  `UNKNOWN_TASK` (11 values remain, ADR-0009).
- The engine maps provider responses to states exactly once; `solve()`
  translates terminal states into exceptions (it must return a `Result`),
  `get_task_result()` exposes the same states raw. Single truth, two
  honest presentations.

## Rationale

- A question that throws forces armor around every poll iteration;
  total answers make reclaim loops clean.
- "No such task" is information about the world, not a caller bug — and
  after process restarts with persisted ids, an UNKNOWN answer is the
  *expected* outcome worth handling as data.

## Alternatives considered

- **All outcomes raise** (solve-parity): rejected; armored polling
  loops.
- **Mixed** (UNKNOWN raises as caller bug, UNSOLVABLE returned):
  rejected; adjacent cases, two mechanisms, easy to misremember.
- **Keep `UnknownTaskError` for solve() only**: rejected; solve() on an
  unknown task is impossible (ids originate from the engine), so the
  class would be dead code.
