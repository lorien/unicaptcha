# ADR-0032: TaskStatus split from Result

**Status:** Accepted (amended by ADR-0050: four states, UNKNOWN as returned status; amended by ADR-0056: `result` field replaced by `solution`/`cost`/`raw`, no submission metadata)
**Date:** 2026-08-23

## Context

The single-shot `get_task_result` originally returned the same `Result[T]`
with `status: PENDING | READY` and solution populated only when ready.
This forces `solution: T | None` onto the entire generic Result class —
an always-None-check weakening every `solve()` annotation for one cold-path
method.

## Decision

- `solve()` returns `Result[T]` with **non-optional `solution`**.
- The single-shot query returns a separate lightweight **`TaskStatus`**
  (non-generic, per ADR-0056): `task_id`, `provider`, `status`
  (four states), `solution: BaseSolution | None` populated only when
  READY, plus `cost` and `raw`. Optionality here is honest: it is the
  point of the call.
- Per ADR-0050, `status` has four values: PENDING, READY, UNSOLVABLE,
  UNKNOWN — provider-side outcomes are returned, not raised.

## Rationale

- Hot path keeps maximum type strength; cold path's optional result
  reflects genuine uncertainty rather than leaking into everything.
- One type per question: "give me the solution" vs "what is the state".

## Alternatives considered

- **One Result with status field**: rejected; weakens the primary API's
  typing guarantee.
- **Pending queries returning None**: rejected; None-checking loses
  task_id/provider context and forces a second call for it.
