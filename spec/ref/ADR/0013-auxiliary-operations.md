# ADR-0013: Auxiliary operations

**Status:** Accepted (amended twice: routing via TaskRef instead of bare ids/TaskResult; four-state status semantics per ADR-0050; `report_good_result` added per ADR-0068; renamed 2026-08-24: `get_task_result` → `get_task_status`, `TaskStatus` → `TaskStatusResult`; amended 2026-08-24: `report_bad_result` returns `bool` symmetric with `report_good_result`; `abandoned_tasks()` → `get_abandoned_tasks()`, registry row added)
**Date:** 2026-08-22, amendment 2026-08-24

## Context

Beyond solving, providers expose balance checks, bad-solution reports, and
task-status queries. On a multi-provider client, "whose balance?" and "which
provider's task 42?" must be answerable. An early design routed task ops via
typed `TaskResult` arguments; that conflated operations and made abandoned-task
reclaim (no TaskResult exists) impossible.

## Decision

All three operations exist on both tiers:

| Operation | Universal client | Facade |
|---|---|---|
| `get_balance(...)` | discriminator: provider instance / class / provider string (all three accepted, normalized internally) | implicit provider |
| `get_task_status(task)` | `TaskRef` | `int \| TaskRef` |
| `report_bad_result(task)` | `TaskRef` | `TaskRef \| int` (returns bool, symmetric with report_good_result) |
| `report_good_result(task)` | `TaskRef` | `TaskRef \| int` (ADR-0068; returns bool) |
| `get_abandoned_tasks()` | snapshot `tuple[TaskRef, ...]` | same |

- `get_balance()` returns `Decimal`, pinned to USD (ADR-0040).
- `report_bad_result` and `report_good_result` are uniform methods
  everywhere, both returning **`bool`** (provider accepted the report or
  not — symmetric with the `parse_report_*` adapter layer, ADR-0068);
  adapters enforce the per-provider/per-kind support
  matrix pre-flight for both, raising
  `UnsupportedChallengeError` where coverage is missing — client-side,
  no network traffic (ADR-0057, ADR-0068; probe-by-exception;
  introspection deferred). Good reports feed worker quality routing
  on providers that accept them.
- `get_abandoned_tasks()` returns a snapshot tuple of the abandoned-task
  registry (ADR-0038/0060), surviving close.
- `get_task_status` returns `TaskStatusResult` with four states
  (PENDING/READY/NO_SOLUTION/UNKNOWN) — provider outcomes are returned
  values, never exceptions (ADR-0050).
- All task-addressing arguments are validated pre-flight: a `TaskRef` whose
  provider does not match the facade (or is missing from the registry)
  raises `TypeError` with both parties named; no network traffic occurs
  (ADR-0045).
- Aux ops share the submission retry policy (ADR-0011).

## Rationale

- `TaskRef` carries routing; ids alone are ambiguous on multi-provider
  clients, and `TaskResult`-routed `get_task_status` was circular (you already
  had the result).
- Facades may accept bare ints because their provider is implicit; the
  universal client cannot.
- Uniform naming across tiers (`report_bad_result`, `get_task_status`,
  `get_balance`) — one vocabulary.

## Alternatives considered

- **`get_task_status(result: TaskResult)`**: superseded; circular semantics,
  blocked abandoned-task reclaim.
- **`report_bad_result` + `report_bad_result_id` pair**: superseded by the
  single-name, typed-union signature (owner decision).
- **`report_bad_task` naming**: rejected mid-discussion; introduced a
  second noun for one act.
- **Per-capability methods mirroring provider endpoints** (Anti-Captcha's
  `reportIncorrectImageCaps` style): rejected; loses the uniform surface.
