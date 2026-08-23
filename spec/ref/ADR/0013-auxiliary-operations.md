# ADR-0013: Auxiliary operations

**Status:** Accepted (amended twice: routing via TaskRef instead of bare ids/Result; four-state status semantics per ADR-0050)
**Date:** 2026-08-22

## Context

Beyond solving, providers expose balance checks, bad-solution reports, and
task-status queries. On a multi-provider client, "whose balance?" and "which
provider's task 42?" must be answerable. An early design routed task ops via
typed `Result` arguments; that conflated operations and made abandoned-task
reclaim (no Result exists) impossible.

## Decision

All three operations exist on both tiers:

| Operation | Universal client | Facade |
|---|---|---|
| `get_balance(...)` | discriminator: provider instance / class / provider string (all three accepted, normalized internally) | implicit provider |
| `get_task_result(task)` | `TaskRef` | `int \| TaskRef` |
| `report_bad_result(task)` | `TaskRef` | `TaskRef \| int` |

- `get_balance()` returns `Decimal`, pinned to USD (ADR-0040).
- `report_bad_result` is a uniform method everywhere; adapters enforce the
  per-provider/per-kind support matrix, raising `UnsupportedCaptchaError`
  where coverage is missing (probe-by-exception; introspection deferred).
- `get_task_result` returns `TaskStatus` with four states
  (PENDING/READY/UNSOLVABLE/UNKNOWN) — provider outcomes are returned
  values, never exceptions (ADR-0050).
- All task-addressing arguments are validated pre-flight: a `TaskRef` whose
  provider does not match the facade (or is missing from the registry)
  raises `TypeError` with both parties named; no network traffic occurs
  (ADR-0045).
- Aux ops share the submission retry policy (ADR-0011).

## Rationale

- `TaskRef` carries routing; ids alone are ambiguous on multi-provider
  clients, and `Result`-routed `get_task_result` was circular (you already
  had the result).
- Facades may accept bare ints because their provider is implicit; the
  universal client cannot.
- Uniform naming across tiers (`report_bad_result`, `get_task_result`,
  `get_balance`) — one vocabulary.

## Alternatives considered

- **`get_task_result(result: Result)`**: superseded; circular semantics,
  blocked abandoned-task reclaim.
- **`report_bad_result` + `report_bad_result_id` pair**: superseded by the
  single-name, typed-union signature (owner decision).
- **`report_bad_task` naming**: rejected mid-discussion; introduced a
  second noun for one act.
- **Per-capability methods mirroring provider endpoints** (Anti-Captcha's
  `reportIncorrectImageCaps` style): rejected; loses the uniform surface.
