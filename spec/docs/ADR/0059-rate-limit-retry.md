# ADR-0059: Rate-limit responses are retryable

**Status:** Accepted (amended: service-busy payloads added as a retryable condition with dedicated `ServiceBusyError`)
**Date:** 2026-08-23

## Context

deferred.md item 5 promises "`RateLimitError` retry with backoff exists
as a safety net", but ADR-0011's retry lists never mention rate-limit
signals: neither HTTP 429 nor provider rate-limit error payloads
(e.g. ERROR_TOO_MANY_REQUESTS-style codes) appear in the submit-phase
retry list, the fail-fast list, or the aux-op policy. The promised
safety net was unwired.

Rate limiting is knowably transient and safe to retry: unlike a read
timeout, a 429 proves the server received and declined the request
without committing anything — no double-charge risk (the ADR-0011
double-charge analysis does not apply).

## Decision

- **Retryable rate-limit signals**: HTTP **429** and provider
  rate-limit error payloads (mapped by the adapter's
  `map_provider_error`).
- **Retryable service-busy signals** (amendment): provider
  "no workers free" payloads — `ERROR_NO_SLOT_AVAILABLE`
  (2Captcha-family), `ERROR_TOO_MANY_TASKS` (Anti-Captcha),
  provider equivalents — map to a new **`ErrorKind.SERVICE_BUSY`**
  and join the same retry policy: standard backoff (full jitter,
  1-30 s, `max_attempts` via `RetryConfig`), submit phase and aux
  ops; the poll phase already tolerates them. Provider guidance
  ("wait ~5 s") is satisfied by the base backoff — no special-cased
  first delay. One WARNING log per busy retry. On exhaustion raise
  the new **`ServiceBusyError`** leaf — separate from
  `RateLimitError`: identical remediation (retry with backoff), but
  a different terminal diagnosis the caller may act on (e.g. route
  to another provider).
- **Where**: submission phase and auxiliary operations — the same
  scope as other retried failures; the **poll phase already tolerates
  all transient failures** bounded by `total_timeout` (ADR-0011), so
  nothing new there.
- **How**: the standard policy — full-jitter exponential backoff,
  base 1 s, cap 30 s, `max_attempts` (default 3) via `RetryConfig`,
  bounded by `total_timeout` where it applies. No separate rate-limit
  budget or knob.
- **On exhaustion**: raise **`RateLimitError`** (ErrorKind
  RATE_LIMIT). The caller sees the honest terminal diagnosis, not a
  generic network error.
- One WARNING log per rate-limit retry (retryable failure, ADR-0039),
  no credentials in the message.

## Rationale

- Closes the gap between the documented safety net and the actual
  policy without new machinery: rate limits join the existing
  retryable set under the existing budget.
- Knowably-safe retry: 429/declined-without-commit is the polar
  opposite of the ambiguous failures ADR-0011 refuses to retry.

## Alternatives considered

- **Fail fast, no retry**: rejected; converts the documented safety
  net into an immediate error on the first burst.
- **Separate rate-limit budget (own attempts/backoff)**: rejected;
  second knob, second budget interaction with `total_timeout`,
  no demonstrated need.
- **Retry with Retry-After header honor**: deferred with the rest of
  per-response scheduling; full jitter already de-synchronizes bursts.
- **Reuse `ErrorKind.RATE_LIMIT` for busy payloads**: rejected by
  owner; identical retry action, but the terminal diagnosis differs —
  busy means "provider capacity," rate limit means "you are too fast,"
  and callers may route differently.
