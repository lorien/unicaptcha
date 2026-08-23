# ADR-0018: Logging and events

**Status:** Accepted (amended: flat logger only; `failed` phase added; sync handler guard added; two-phase event semantics per ADR-0067 — invariant reworded to "every *waited* solve")
**Date:** 2026-08-22, amendments 2026-08-23

## Context

Observability needs: progress visibility during long solves (events) and
post-hoc debugging (logs). Design questions: handler execution model on the
async side, logger naming, whether terminal failures emit events.

## Decision

**Events.** One typed event type, `SolveEvent` (frozen dataclass), phases:
`submitted`, `poll`, `retry`, `solved`, `failed`. Fields: provider, task_id,
elapsed, attempt, detail, and `error_kind: ErrorKind | None` (failure phase
only). Invariants:

- Every solve ends in exactly one of `solved` or `failed`; the `failed`
  event fires immediately before the terminal raise, for every
  library-raised exception (timeout, unsolvable, network, provider, ...).
  (Amended by ADR-0067 for two-phase: `submitted` fires at submit,
  `solved`/`failed` at wait's terminal state; never-waited tickets are
  eventless — "every *waited* solve ends in exactly one of `solved` or
  `failed`.")
- **Cancellation is eventless**: firing events while unwinding
  `CancelledError` repeats the ADR-0016 mistake; the abandoned-task
  registry is cancellation's observability story.
- Handlers run **inline**: async side awaits awaitable results inside the
  solve coroutine (documented "handlers must be fast" contract — strict
  ordering, handler errors propagate raw, no fire-and-forget tasks); sync
  side calls directly in the solving thread.
- **Sync handler guard**: coroutine-function handlers passed to sync
  clients are rejected at attachment with `InvalidConfigError`
  (`inspect.iscoroutinefunction` with `functools.partial` unwrapping); an
  awaitable returned at runtime by a pathological wrapper logs a WARNING
  and is discarded. Fail fast on the detectable, degrade loudly on the
  rest.
- Attachment: `on_event` accepted at construction and per call; per-call
  replaces client-level all-or-nothing (ADR-0044).

**Logging.** One flat logger, `logging.getLogger("unicaptcha")`, for v1.
Per-instance logger names (`unicaptcha.client-1`) were rejected (logger
objects leak in the stdlib global dict; order-based names are meaningless);
hierarchical component names (`unicaptcha.http`, ...) rejected for now
(deferred.md item 8). Client identity, when needed, travels as message
context (optional client `name`). Full taxonomy in ADR-0039; taxonomy
essentials: nothing logs at ERROR (errors are exceptions; callers decide);
solution tokens never logged at any level.

## Rationale

- Inline execution: events are progress notifications, not work queues;
  strict ordering and visible handler failures beat throughput.
- Flat logger: zero leak, zero naming commitments; per-component filtering
  is speculative until requested.
- `failed` phase: a monitoring handler attached at the constructor must see
  the complete lifecycle; a blind spot at terminal failure defeats the
  purpose.

## Alternatives considered

- **Spawned handler tasks** (no backpressure on solving): rejected;
  ordering not guaranteed, errors vanish, tasks outlive clients.
- **Per-instance child loggers**: rejected; stdlib logger-object leak,
  meaningless names.
- **ERROR-level library logs**: rejected; double-reporting with exceptions.
- **Cancellation event**: rejected; unsafe during unwinding.
