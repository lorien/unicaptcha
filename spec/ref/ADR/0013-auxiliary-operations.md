# ADR-0013: Auxiliary operations

**Status:** Accepted (amended twice: routing via TaskRef instead of bare ids/SolveResult; four-state status semantics per ADR-0050; `report_good_result` added per ADR-0068; renamed 2026-08-24: `get_task_result` → `get_task_status`, `TaskStatus` → `TaskStatusResult`)
**Date:** 2026-08-22, amendment 2026-08-24

## Context

Beyond solving, providers expose balance checks, bad-solution reports, and
task-status queries. On a multi-provider client, "whose balance?" and "which
provider's task 42?" must be answerable. An early design routed task ops via
typed `SolveResult` arguments; that conflated operations and made abandoned-task
reclaim (no SolveResult exists) impossible.

## Decision

All three operations exist on both tiers:

| Operation | Universal client | Facade |
|---|---|---|
| `get_balance(...)` | discriminator: provider instance / class / provider string (all three accepted, normalized internally) | implicit provider |
| `get_task_status(task)` | `TaskRef` | `int \| TaskRef` |
| `report_bad_result(task)` | `TaskRef` | `TaskRef \| int` |
| `report_good_result(task)` | `TaskRef` | `TaskRef \| int` (ADR-0068) |

- `get_balance()` returns `Decimal`, pinned to USD (ADR-0040).
- `report_bad_result` and `report_good_result` are uniform methods
  everywhere; adapters enforce the per-provider/per-kind support
  matrix pre-flight for both, raising
  `UnsupportedCaptchaError` where coverage is missing — client-side,
  no network traffic (ADR-0057, ADR-0068; probe-by-exception;
  introspection deferred). Good reports feed worker quality routing
  on providers that accept them.
- `get_task_status` returns `TaskStatusResult` with four states
  (PENDING/READY/UNSOLVABLE/UNKNOWN) — provider outcomes are returned
  values, never exceptions (ADR-0050).
- All task-addressing arguments are validated pre-flight: a `TaskRef` whose
  provider does not match the facade (or is missing from the registry)
  raises `TypeError` with both parties named; no network traffic occurs
  (ADR-0045).
- Aux ops share the submission retry policy (ADR-0011).

## Rationale

- `TaskRef` carries routing; ids alone are ambiguous on multi-provider
  clients, and `SolveResult`-routed `get_task_status` was circular (you already
  had the result).
- Facades may accept bare ints because their provider is implicit; the
  universal client cannot.
- Uniform naming across tiers (`report_bad_result`, `get_task_status`,
  `get_balance`) — one vocabulary.

## Alternatives considered

- **`get_task_status(result: SolveResult)`**: superseded; circular semantics,
  blocked abandoned-task reclaim.
- **`report_bad_result` + `report_bad_result_id` pair**: superseded by the
  single-name, typed-union signature (owner decision).
- **`report_bad_task` naming**: rejected mid-discussion; introduced a
  second noun for one act.
- **Per-capability methods mirroring provider endpoints** (Anti-Captcha's
  `reportIncorrectImageCaps` style): rejected; loses the uniform surface.
