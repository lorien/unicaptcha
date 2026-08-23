# ADR-0045: TaskRef and pre-flight provider validation

**Status:** Accepted
**Date:** 2026-08-23

## Context

Aux task operations need routing. Typed `Result` arguments worked for
report-bad but made `get_task_result` circular (a Result means the task is
solved) and left abandoned-task reclaim impossible (no Result exists).
Bare ints are ambiguous on multi-provider clients.

## Decision

- **`TaskRef`** — public, constructible, frozen: `TaskRef(provider: str,
  task_id: int)`. The single "thing that points at a task": registry
  entries, reclaim references, persisted-id reconstruction (provider +
  id survive a process restart). No `AbandonedTask` subclass —
  "abandoned" is workflow state, not object shape; registry metadata
  rides alongside.
- Signatures (ADR-0013): universal `get_task_result(TaskRef)`,
  `report_bad_result(TaskRef)`; facades accept `int | TaskRef`.
- `Result.task_ref` convenience property (`TaskRef.of(result)`
  equivalent) so reporting a held Result is one expression.
- **Pre-flight provider validation**: every task-addressing argument is
  checked before any network traffic. A `TaskRef` whose provider does
  not match the facade — or is absent from the universal client's
  registry — raises **`TypeError`** naming both parties
  ("TaskRef belongs to provider 'anti-captcha' but this facade is
  'twocaptcha'"). Same for challenge dispatch. Unknown discriminator
  strings in `get_balance` get the same treatment. The
  `solve(..., provider=...)` discriminator of kind-level solve
  (ADR-0064) is validated the same way: unknown string ->
  `TypeError`; contradicting a concrete challenge's provider ->
  `TypeError` naming both parties.

## Rationale

- Routing identity travels with the reference; ambiguous bare ids are
  confined to facades where the provider is implicit.
- Pre-flight validation turns "confusing `ProviderError`/`UNKNOWN` from
  the wrong service" into an immediate, local, explanatory error —
  consistent with the wrong-provider-challenge `TypeError` precedent.

## Alternatives considered

- **`(task_id, provider)` two-argument overload**: rejected; signature
  bloat, two loose values where one typed object carries both.
- **Result-accepting `get_task_result`**: superseded; circular.
- **Validation deferred to provider**: rejected; wrong-service queries
  surface as opaque provider errors.
