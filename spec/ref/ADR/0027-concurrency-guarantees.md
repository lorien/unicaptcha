# ADR-0027: Concurrency guarantees

**Status:** Accepted
**Date:** 2026-08-23

## Context

Callers share client instances: async clients across tasks, sync clients
across threads. The library must either document supported sharing or
engineer locks.

## Decision

- **Async clients**: safe to share across concurrent tasks. httpx
  AsyncClient supports it; per-solve state lives in local variables.
- **Sync clients**: safe to share across threads. httpx sync client is
  thread-safe for requests; the solve flow holds no shared mutable state
  beyond config and the registry (whose storage is lock-guarded,
  ADR-0038).
- These guarantees are **documented as the supported usage** rather than
  backed by additional locking; the design keeps shared state minimal by
  construction.
- CI additionally runs the test suite on free-threaded 3.14t
  (informational) where the GIL would not mask registry/lifecycle races
  (ADR-0047).

## Rationale

- One client = one connection pool is the resource-efficient pattern;
  making it unsafe would force per-task clients.
- Minimal shared state + locks only where mutation exists (registry) is
  cheaper and more honest than blanket synchronization.

## Alternatives considered

- **No sharing; one client per task/thread**: rejected; wasteful and
  surprising.
- **Full internal locking**: rejected; unnecessary given state layout.
