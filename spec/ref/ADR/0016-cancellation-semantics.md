# ADR-0016: Cancellation semantics

**Status:** Accepted (supersedes the original SolveCancelledError design)
**Date:** 2026-08-22, redesigned 2026-08-23

## Context

The original design caught `asyncio.CancelledError` mid-solve and raised a
custom `SolveCancelledError` carrying the abandoned `task_id`. Review found
this violates asyncio's cancellation protocol: `asyncio.timeout()`
converts an inner cancellation into `TimeoutError` only if `CancelledError`
propagates; TaskGroup structured concurrency, `wait_for`, and anyio scopes
all rely on faithful propagation. Swallowing it corrupts the very machinery
our own `total_timeout` design depends on.

## Decision

- **`CancelledError` propagates untouched** — never caught, never
  substituted. `SolveCancelledError` does not exist in the hierarchy.
- The abandoned task's id is preserved via the **abandoned-task registry**
  (ADR-0038): at submission the client records the task id; on successful
  delivery the entry is removed; after cancellation the entry remains.
  Registry updates are **pure-synchronous** (no awaits) so they are safe
  during cancellation unwinding.
- Callers reclaim paid-for answers later via `get_task_status(TaskRef)`.
- Billing caveat documented: abandoned tasks may still be billed; the
  library makes them reclaimable, not refundable.
- Internal timeout: the solve runs inside `asyncio.timeout()`; the
  resulting `TimeoutError` is converted to `TaskTimeoutError` at our scope
  boundary only. External cancellations pass through the scope machinery
  untouched — exactly the discrimination the stdlib provides.
- Sync side: `KeyboardInterrupt` propagates naturally; nothing to design.

## Rationale

- Library-design rule (stated in anyio's docs among others): a coroutine
  must let `CancelledError` escape. Composability with caller-side timeout
  scopes and task groups outweighs any exception-typing nicety.
- The registry delivers the original motivation (recovering paid-for task
  ids) without touching the protocol.

## Alternatives considered

- **`SolveCancelledError(task_id=...)`**: removed; breaks `asyncio.timeout`,
  TaskGroup, wait_for, anyio scopes; contradicted our own timeout design.
- **Cleanup calls during cancellation**: rejected; awaiting anything while
  unwinding cancellation is itself fragile; must stay fast and predictable.
