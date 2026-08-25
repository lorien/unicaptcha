# ADR-0033: Client lifecycle

**Status:** Accepted (amended 2026-08-23: shutdown-event close semantics; registry survives close; recovery workflow per ADR-0060)
**Date:** 2026-08-23

## Context

Clients hold connection pools. Closing protocols, ownership of injected
httpx clients, use-after-close behavior, and — a gap found in review —
`close()` racing in-flight solves. Sync solves block up to `total_timeout`;
a naive `close()` either refuses, waits minutes, or leaks. The owner
proposed the resolution: a `threading.Event` the solve loop cooperatively
watches.

## Decision

**Basics.**

- Explicit `close()` (sync) / `aclose()` (async), **idempotent**.
- Context managers on all clients and facades (`__enter__/__exit__`,
  `__aenter__/__aexit__`), returning self.
- Eager httpx construction at `__init__` (no lazy init races).
- Any operation after close raises `ClientClosedError` (typed leaf in the
  hierarchy; callers stay within one exception family).
- Ownership by construction path: library-built HTTP layer → we close it;
  injected httpx client → caller owns, we never close it (ADR-0024,
  ADR-0049).

**Close with in-flight solves.**

- Sync: clients hold a `threading.Event` shutdown flag. Sleeps are
  implemented as `shutdown.wait(timeout=...)`; every loop iteration checks
  the flag. `close()` sets the event: blocked solves wake at their next
  checkpoint — close latency is **at most one in-flight HTTP round trip**
  instead of up to `total_timeout`. Interrupted solves raise
  `ClientClosedError`; their task ids enter the abandoned-task registry.
- Async: `aclose()` cancels in-flight solve tasks (clean
  `CancelledError` propagation per ADR-0016), registry captures ids,
  connections close.
- The injectable clock/sleep seam (implementation detail) makes the
  event-wait sleep the default sync implementation at near-zero cost.

**Registry interaction.**

- The abandoned-task registry **survives close** (supersedes an earlier
  "cleared on close"): `get_abandoned_tasks()` remains readable afterward;
  entries are removed only by terminal-state reclaim (ADR-0038). This
  gives close-then-reclaim a working story for tasks that may already be
  billed.

## Rationale

- The shutdown event turns "blocked threads cannot be interrupted" into
  "our own cooperative loops can be woken" — we own every checkpoint.
- Idempotency + typed closed-error + eager construction eliminate the
  classic lifecycle footguns (double close, first-use races, silent
  use-after-close).

## Alternatives considered

- **Refuse to close while busy**: rejected; caller-side bookkeeping,
  check/close races.
- **Block until solves finish**: rejected pre-amendment; up to 120 s
  waits.
- **`close(force=...)` flags**: rejected; two code paths x two tiers;
  the event mechanism makes force unnecessary.
- **`RuntimeError` on use-after-close**: rejected; outside the hierarchy.
