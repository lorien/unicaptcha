# ADR-0017: No client-side rate limiting

**Status:** Accepted
**Date:** 2026-08-23

## Context

Providers throttle abusive clients and bill per solve. Candidate mechanisms:
per-provider concurrency semaphores (`max_parallel_solves`), minimum request
spacing, token buckets.

## Decision

No client-side rate limiting or concurrency caps in v1. Callers manage their
own concurrency (semaphores, queues, task groups); the library's
`RateLimitError` retry with backoff (ADR-0011) is the safety net. README
documents this guidance explicitly.

## Rationale

- Owner decision: keep v1 minimal; the library cannot guess acceptable
  concurrency across use cases.
- Full rate limiters are rarely needed: polling dominates request volume
  and is self-spaced by `poll_interval`.

## Alternatives considered

- **Optional `max_parallel_solves` semaphore**: rejected for v1.
- **Token-bucket / request spacing**: rejected; machinery without a
  driving use case.
