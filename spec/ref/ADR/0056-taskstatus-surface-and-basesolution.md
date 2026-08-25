# ADR-0056: TaskStatusResult surface — no SolveResult, no submission metadata; BaseSolution root

**Status:** Accepted (amends ADR-0032, ADR-0035; supersedes the `result: SolveResult[T] | None` field of TaskStatusResult; complements ADR-0050; renamed 2026-08-24: object `TaskStatus` → `TaskStatusResult`, enum `TaskState` → `TaskStatus`, `get_task_result` → `get_task_status`)
**Date:** 2026-08-23, amendment 2026-08-24

## Context

ADR-0032 gave `TaskStatusResult` a `result: SolveResult[T] | None` field. Two flaws:

1. **Unbindable generic.** `get_task_status(task: TaskRef)` carries no
   type parameter — the `T` in `TaskStatusResult.result` can never be bound
   by the signature. In a mypy/pyright-strict library (goal 3) this is
   a type that lies.
2. **Dishonest metadata.** `SolveResult` requires non-optional `created_at`
   and `elapsed` (ADR-0008, ADR-0034) — submission-time facts. But the
   primary `get_task_status` caller reclaims tasks with no submission
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
- **`TaskStatusResult` is non-generic** and carries what the provider
  response actually carries:

| Field | Type |
|---|---|
| `task_id` | `int` |
| `provider` | `str` |
| `status` | `TaskStatus` — new enum: `PENDING`, `READY`, `NO_SOLUTION`, `UNKNOWN` (ADR-0050) |
| `solution` | `BaseSolution \| None` — populated only when READY; narrow via isinstance |
| `cost` | `Decimal \| None` |
| `raw` | `bytes` — untouched response body |

- **No `created_at`, no `elapsed`** on TaskStatusResult — deliberately, not
  as None-able fields. Submission metadata exists exactly where
  submission context exists: `SolveResult[T]` from `solve()`. One honest
  shape serves same-client and post-restart reclaim alike.
- **`SolveResult[T]` is the solve()-only return**; `TaskStatusResult` never
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

- **Keep `result: SolveResult[T] | None`, bind T via generic method
  (`get_task_status(ref) -> TaskStatusResult[T]`)**: rejected; the caller
  cannot name T — the TaskRef carries no type information; any
  annotation would be cast-theater.
- **SolveResult with None-able `created_at`/`elapsed`**: rejected; weakens
  the solve()-path guarantee (ADR-0032's whole point) or forks a
  second SolveResult variant.
- **TaskStatusResult keeps only status + ids, solution fetched separately**:
  rejected; READY would then cost two round trips, and the response
  already holds the solution.
