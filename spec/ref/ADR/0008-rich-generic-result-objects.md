# ADR-0008: Rich generic result objects

**Status:** Accepted (amended: solution typing via kind bases; metadata set ratified in ADR-0034; non-optional solution reaffirmed in ADR-0032; renamed 2026-08-24: `Result[T]` → `SolveResult[T]` → `TaskResult[T]` — task-centric vocabulary)
**Date:** 2026-08-22

## Context

A solve call must return more than a bare token: callers need cost, task id,
raw payload, timing. The result must type precisely per captcha kind, and
must not degrade into optional-everywhere bags.

## Decision

`solve()` returns `TaskResult[T]` where `T` is the solution type:

- `solution: T` — **non-optional**; a returned TaskResult always carries its
  solution (pending states never masquerade as results; single-shot status
  queries return `TaskStatusResult` instead, ADR-0032).
- `task_id: int` — all four providers use integer task ids.
- `cost: Decimal | None` — `Decimal(str(raw_value))`; money is parsed as
  exact decimal, never float; None when the provider does not report cost.
- `raw: bytes` — untouched response body (uniform "raw = verbatim HTTP
  body" convention with `error.raw_response`, ADR-0034).
- metadata: `provider: str`, `created_at: datetime` (UTC-aware),
  `elapsed: timedelta` (ADR-0034).
- `task_ref` convenience property -> `TaskRef` for aux-op addressing
  (ADR-0045).

Solution typing uses generics with inheritance-based solution classes
(ADR-0035): abstract kind bases (`ImageSolution`, ...) with provider
subclasses adding extras. No stringification shortcut: the result object
does not pretend to be the token.

## Rationale

- Rich results serve cost monitoring, reclaim flows, and debugging without
  extra round trips (raw payload attached).
- `Decimal` for money: providers return string/float prices; binary float
  sums drift, Decimal does not.
- Generics + non-optional solution give static checkers full strength on
  the hot path.

## Alternatives considered

- **Bare token/string returns**: rejected; loses task id/cost/raw needed by
  report-bad and reclaim flows.
- **TaskResult that stringifies to the token**: rejected by owner decision.
- **One result class with union-typed solution**: rejected; weaker typing.
- **`float` cost**: rejected; monetary drift.
- **`status` field on TaskResult with optional solution**: rejected (ADR-0032);
  it would weaken every `solve()` annotation for one cold-path method.
