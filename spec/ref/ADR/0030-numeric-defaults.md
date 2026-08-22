# ADR-0030: Numeric defaults

**Status:** Accepted
**Date:** 2026-08-23

## Context

Poll intervals, timeouts, retry counts, and backoff parameters need
ratified concrete values. Defaults differ by challenge kind (reCAPTCHA-class
tasks take far longer than image/text tasks).

## Decision

The engine's per-kind default table:

| Parameter | reCAPTCHA v2/v3, hCaptcha | image / text |
|---|---|---|
| poll interval | 5 s | 2 s |
| total_timeout (default) | 120 s | 30 s |
| per-request HTTP timeout | 20 s | 20 s |
| submit retry attempts (total) | 3 | 3 |
| backoff | full jitter, base 1 s, cap 30 s | same |

- All values overridable at client level and per call via the None-merge
  chain (ADR-0043).
- The table is extended by custom adapters' `default_solve_config`
  declarations with a generic fallback for adapters that declare none
  (ADR-0041).
- Kinds not in the table and not declared by the adapter receive the
  generic fallback (conservative: 120 s / 5 s).

## Rationale

- Numbers follow provider guidance (reCAPTCHA-class: poll ~5 s, solve up
  to ~2 min; images: fast, ~2 s polls, 30 s is ample).
- Provider-recommended poll intervals avoid the too-fast-polling
  rate-limit trap.

## Alternatives considered

- **One default set for all kinds**: rejected; 120 s waits for images or
  30 s ceilings for reCAPTCHA would both be wrong.
- **Per-provider defaults**: rejected; timing is a property of the
  captcha kind, not the service.
