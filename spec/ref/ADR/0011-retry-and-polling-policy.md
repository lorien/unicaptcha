# ADR-0011: Retry and polling policy

**Status:** Accepted (amended 2026-08-23: refined retry scope by failure knowledge; full jitter added; aux-op parity settled; rate-limit retryability added per ADR-0059)
**Date:** 2026-08-22

## Context

Retrying a `createTask` submission whose outcome is unknown can create (and
bill) a second task. HTTP 5xx codes differ in what they prove: a received
500/503 means the server itself failed before commit; a 502/504 from a
reverse proxy may mask a successful origin outcome. Polling requests are
safe to retry freely (a lost response costs nothing). Aux operations were
initially candidates for a reduced policy.

## Decision

**Submission phase** — retry only provably-safe failures:

- **Retry**: pre-send failures (DNS, connection refused, TLS handshake,
  connect-timeout), received **500 / 503**, and **rate-limit signals**
  (HTTP 429, provider rate-limit payloads; `RateLimitError` on
  exhaustion, ADR-0059).
- **Fail fast** (`NetworkError`, no resubmit): read timeouts,
  connection reset after send, **502 / 504** (gateway errors may mask a
  committed origin request).
- Backoff: exponential with **full jitter**, base 1 s, cap 30 s, max 3
  attempts total; all configurable via `RetryConfig` (None-merge chain).
- Ambiguous-failure tasks are documented as rare paid-but-orphaned cases
  (same category as abandoned tasks).

**Polling phase** — tolerate all transient failures (network errors, 5xx):
a failed poll never aborts the solve; retries continue bounded by
`total_timeout`. Only budget exhaustion or terminal provider states
(READY / UNSOLVABLE) end the loop.

**Auxiliary operations** — same policy as submission, uniformly, for
consistency (owner decision over a reduced/single-retry variant).

## Rationale

- The refined split follows one principle: retry only when the outcome is
  *knowably* "nothing happened".
- Full jitter de-synchronizes concurrent clients retrying a shared 503;
  one line, strictly better under load.
- One policy across all operations avoids per-operation tuning knobs and
  mixed-traffic surprises.

## Alternatives considered

- **Retry all network errors + blanket 5xx**: original proposal; rejected
  after the double-charge analysis (read timeouts, 502/504 ambiguous).
- **Reduced aux-op retry (single attempt) / no aux retries**: rejected;
  consistency chosen.
- **Plain exponential (no jitter)**: rejected; synchronized retry waves.
- **Auto-resubmit on UNSOLVABLE**: rejected (ADR-0029); caller decides.
