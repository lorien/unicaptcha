# ADR-0029: UnsolvableCaptchaError, no auto-resubmit

**Status:** Accepted
**Date:** 2026-08-23

## Context

All three services can answer "workers could not solve this"
(`ERROR_CAPTCHA_UNSOLVABLE` and equivalents). This is a common, distinct
terminal outcome — not a generic provider error — and callers often want to
retry with a fresh task. The library could resubmit automatically.

## Decision

- Dedicated **`UnsolvableCaptchaError`** exception (`ErrorKind.UNSOLVABLE`),
  distinct from the catch-all `ProviderError`.
- **No auto-resubmit option** in v1: `solve()` raises; the caller decides
  whether/how to retry. (Related: status queries return UNSOLVABLE as a
  state, ADR-0050.)
- Documented billing note: unsolved image/text tasks are typically not
  billed; abandoned polling tasks may be.

## Rationale

- Retrying is a policy (new challenge? new provider? backoff?); the
  library must not own policy.
- A dedicated class makes `except UnsolvableCaptchaError` retry loops
  trivial without string-matching provider messages.

## Alternatives considered

- **Map to `ProviderError`**: rejected; forces message-sniffing for the
  most common retryable outcome.
- **Auto-resubmit N times**: rejected; hidden cost doubling, policy
  creep.
