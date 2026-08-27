# ADR-0029: NoSolutionError, no auto-resubmit

**Status:** Accepted (renamed 2026-08-24: class `UnsolvableCaptchaError` → `UnsolvableChallengeError` → `NoSolutionError`, `ErrorKind.UNSOLVABLE` → `UNSOLVABLE_CHALLENGE` → `NO_SOLUTION`; status-enum member `TaskStatus.UNSOLVABLE` → `TaskStatus.NO_SOLUTION` — one word `NO_SOLUTION` for the outcome across both status and error enums, paired with `EmptySolutionError` rather than the call-shape Challenge family; amended 2026-08-24: provider count three → four per ADR-0071)
**Date:** 2026-08-23, amendments 2026-08-24

## Context

All four services can answer "workers could not solve this"
(`ERROR_CAPTCHA_UNSOLVABLE` and equivalents). This is a common, distinct
terminal outcome — not a generic provider error — and callers often want to
retry with a fresh task. The library could resubmit automatically.

## Decision

- Dedicated **`NoSolutionError`** exception (`ErrorKind.NO_SOLUTION`),
  distinct from the catch-all `ProviderError`.
- **No auto-resubmit option** in v1: `solve()` raises; the caller decides
  whether/how to retry. (Related: status queries return NO_SOLUTION as a
  state, ADR-0050.)
- Documented billing note: unsolved image/text tasks are typically not
  billed; abandoned polling tasks may be.

## Rationale

- Retrying is a policy (new challenge? new provider? backoff?); the
  library must not own policy.
- A dedicated class makes `except NoSolutionError` retry loops
  trivial without string-matching provider messages.

## Alternatives considered

- **Map to `ProviderError`**: rejected; forces message-sniffing for the
  most common retryable outcome.
- **Auto-resubmit N times**: rejected; hidden cost doubling, policy
  creep.
