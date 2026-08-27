# ADR-0044: Event handler attachment

**Status:** Accepted (amended 2026-08-24: `on_event` also accepted on `submit()` per ADR-0067/0051 parity — emits SUBMIT_REQUESTED/SUBMIT_ACCEPTED/SUBMIT_FAILED)
**Date:** 2026-08-23, amendment 2026-08-24

## Context

Handlers are per-solve progress (a UI tick) or client-wide observability
(a logger). Attachment options: per-call only, constructor only, or both.

## Decision

- `on_event` is accepted at **both** levels: client constructor and every
  solve call — universal `solve()`, facade convenience methods
  (ADR-0051), and `submit()` (which emits SUBMIT_REQUESTED/SUBMIT_ACCEPTED/
  SUBMIT_FAILED; two-phase `wait()` uses the client-level handler, amended
  2026-08-24 per ADR-0067/ADR-0051 parity).
- **Per-call overrides client-level, all-or-nothing** — the per-call
  handler replaces the client handler for that call; no chaining, no
  composition. (A composition helper can be added later if wanted.)
- Resolution: `handler = call_handler if call_handler is not None else
  client_handler`.
- Execution semantics per ADR-0018: inline, awaited-if-awaitable (async),
  direct call (sync), sync-client coroutine-function guard.

## Rationale

- Mirrors the config override architecture exactly: defaults at
  construction, overrides at call — one mental model across the library.
- Covers both usage styles: set-once logging handler vs ad-hoc per-solve
  handlers.
- All-or-nothing is the simplest honest semantic for a single value;
  handler chaining is speculative.

## Alternatives considered

- **Per-call only**: rejected; "log every solve" would need the handler
  repeated at every call site, with silent gaps where forgotten.
- **Client-level only**: rejected; no per-solve opt-in/opt-out
  granularity.
- **Chained handlers (call + client both fire)**: rejected; ordering and
  error semantics multiply for no v1 demand.
