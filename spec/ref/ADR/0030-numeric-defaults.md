# ADR-0030: Numeric defaults

**Status:** Accepted (amended: table gains FunCaptcha / GeeTest v3 / GeeTest v4 rows per ADR-0070 — values at implementation, GeeTest/FunCaptcha class near reCAPTCHA cadence; `poll_delay` initial-wait column added)
**Date:** 2026-08-23

## Context

Poll intervals, timeouts, retry counts, and backoff parameters need
ratified concrete values. Defaults differ by challenge kind (reCAPTCHA-class
tasks take far longer than image/text tasks).

## Decision

The engine's per-kind default table:

| Parameter | reCAPTCHA v2/v3, hCaptcha | image / text |
|---|---|---|
| poll delay (before first poll) | 15 s | 5 s |
| poll interval | 5 s | 2 s |
| total_timeout (default) | 120 s | 30 s |
| per-request HTTP timeout | 20 s | 20 s |
| submit retry attempts (total) | 3 | 3 |
| backoff | full jitter, base 1 s, cap 30 s | same |

- **`poll_delay`** (amendment, from second-pass competitive analysis):
  the initial wait after submission before the first `getTaskResult`
  — first-useful-poll approximates typical solve time (competitors'
  operational data: image ~5 s, reCAPTCHA-class ~15-20 s). Applies
  always in `solve()`; in `wait(ticket)` only when the ticket is
  **fresh** (submitted less than one `poll_interval` ago — stale
  tickets poll immediately); never in `wait_ref`/`get_task_result`
  (reconstruction assumes the task may be mature). Counted within
  `total_timeout`. FunCaptcha/GeeTest rows: near reCAPTCHA cadence
  (~15 s); exact values at implementation.
- Generic fallback gains `poll_delay` ~10 s.

- All values overridable at client level and per call via the None-merge
  chain (ADR-0043).
- The table is extended by custom adapters' `default_solve_config`
  declarations with a generic fallback for adapters that declare none
  (ADR-0041).
- Kinds not in the table and not declared by the adapter receive the
  generic fallback (conservative: 120 s total / 5 s interval / 10 s delay).

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
