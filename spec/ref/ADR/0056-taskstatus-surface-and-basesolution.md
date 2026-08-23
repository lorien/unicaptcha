# ADR-0056: TaskStatus surface — no Result, no submission metadata; BaseSolution root

**Status:** Accepted (amends ADR-0032, ADR-0035; supersedes the `result: Result[T] | None` field of TaskStatus; complements ADR-0050)
**Date:** 2026-08-23

## Context

ADR-0032 gave `TaskStatus` a `result: Result[T] | None` field. Two flaws:

1. **Unbindable generic.** `get_task_result(task: TaskRef)` carries no
   type parameter — the `T` in `TaskStatus.result` can never be bound
   by the signature. In a mypy/pyright-strict library (goal 3) this is
   a type that lies.
2. **Dishonest metadata.** `Result` requires non-optional `created_at`
   and `elapsed` (ADR-0008, ADR-0034) — submission-time facts. But the
   primary `get_task_result` caller reclaims tasks with no submission
   context: post-close or post-restart, on a fresh client, via a
   persisted `TaskRef` (ADR-0050, ADR-0045). The adapter parsing a
   `getTaskResult` response cannot know them; only the submitting
   engine does, and only while it lives.

Separately, the solution taxonomy lacked a root: challenges have the
open `BaseChallenge` (ADR-0048) but custom kinds subclassing it had no
solution base to subclass — the claimed symmetry was half true, and
without a root there is no honest non-generic field type for "some
solution" on a status query.

## Decision

- **`BaseSolution`** — public abstract root over the solution kind
  bases, non-instantiable by the same enforcement as all bases
  (ADR-0035). Custom-kind solutions subclass it; the taxonomy is now
  symmetric with `BaseChallenge`.
- **`TaskStatus` is non-generic** and carries what the provider
  response actually carries:

| Field | Type |
|---|---|
| `task_id` | `int` |
| `provider` | `str` |
| `status` | `TaskState` — new enum: `PENDING`, `READY`, `UNSOLVABLE`, `UNKNOWN` (ADR-0050) |
| `solution` | `BaseSolution \| None` — populated only when READY; narrow via isinstance |
| `cost` | `Decimal \| None` |
| `raw` | `bytes` — untouched response body |

- **No `created_at`, no `elapsed`** on TaskStatus — deliberately, not
  as None-able fields. Submission metadata exists exactly where
  submission context exists: `Result[T]` from `solve()`. One honest
  shape serves same-client and post-restart reclaim alike.
- **`Result[T]` is the solve()-only return**; `TaskStatus` never
  embeds it.

## Rationale

- A generic that cannot bind is a documented lie; `BaseSolution` +
  isinstance narrowing is honest on a cold path where the caller
  dispatches on state anyway.
- Optional-when-known metadata (`created_at=None` on a reclaim) would
  be a third None-semantics ("unknown here") beyond "unspecified"
  (ADR-0043) — worse than absence.
- The root completes the challenge/solution symmetry and gives
  custom-kind authors their base.

## Alternatives considered

- **Keep `result: Result[T] | None`, bind T via generic method
  (`get_task_result(ref) -> TaskStatus[T]`)**: rejected; the caller
  cannot name T — the TaskRef carries no type information; any
  annotation would be cast-theater.
- **Result with None-able `created_at`/`elapsed`**: rejected; weakens
  the solve()-path guarantee (ADR-0032's whole point) or forks a
  second Result variant.
- **TaskStatus keeps only status + ids, solution fetched separately**:
  rejected; READY would then cost two round trips, and the response
  already holds the solution.
