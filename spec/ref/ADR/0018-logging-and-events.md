# ADR-0018: Logging and events

**Status:** Accepted (amended: flat logger only; `failed` phase added; sync handler guard added; two-phase event semantics per ADR-0067 — invariant reworded to "every *waited* solve"; renamed 2026-08-24: `SolveEvent` → `TaskEvent`, `SolvePhase` → `TaskPhase` per the task-centric vocabulary; amended 2026-08-24: field `phase` → `kind`, enum `TaskPhase` → `TaskEventKind` — the field names *what event just happened*, not a task stage; set becomes PRE_FLIGHT_FAILED / SUBMIT_REQUESTED / SUBMIT_ACCEPTED / SUBMIT_FAILED / RESULT_REQUESTED / RESULT_RECEIVED / RESULT_FAILED)
**Date:** 2026-08-22, amendments 2026-08-23, 2026-08-24

## Context

Observability needs: progress visibility during long solves (events) and
post-hoc debugging (logs). Design questions: handler execution model on the
async side, logger naming, whether terminal failures emit events.

## Decision

**Events.** One typed event type, `TaskEvent` (frozen dataclass). The
discriminating field is `kind: TaskEventKind` — what just happened:
`PRE_FLIGHT_FAILED`, `SUBMIT_REQUESTED`, `SUBMIT_ACCEPTED`,
`SUBMIT_FAILED`, `RESULT_REQUESTED`, `RESULT_RECEIVED`, `RESULT_FAILED`.
Fields: provider, task_id, elapsed, attempt, detail, and
`error_kind: ErrorKind | None` (set only on the terminal failure kinds).
Invariants:

- Every solve invocation ends in exactly one terminal event:
  `PRE_FLIGHT_FAILED`, `SUBMIT_FAILED`, `RESULT_FAILED`, or
  `RESULT_RECEIVED`. The terminal failure kinds fire immediately before
  the terminal raise, for every library-raised exception (timeout,
  no-solution, network, provider, ...). `PRE_FLIGHT_FAILED` covers
  caller-side faults before any submit attempt (invalid/unsupported
  challenge, config, closed client, wrong-provider `TypeError`).
  (Amended by ADR-0067 for two-phase: `SUBMIT_ACCEPTED` fires at
  submit, `RESULT_RECEIVED`/`RESULT_FAILED` at wait's terminal state;
  never-waited tickets are eventless.)
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
- Terminal failure kinds: a monitoring handler attached at the constructor
  must see the complete lifecycle; a blind spot at terminal failure defeats
  the purpose.

## Alternatives considered

- **Spawned handler tasks** (no backpressure on solving): rejected;
  ordering not guaranteed, errors vanish, tasks outlive clients.
- **Per-instance child loggers**: rejected; stdlib logger-object leak,
  meaningless names.
- **ERROR-level library logs**: rejected; double-reporting with exceptions.
- **Cancellation event**: rejected; unsafe during unwinding.
