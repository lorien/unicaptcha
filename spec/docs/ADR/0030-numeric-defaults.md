# ADR-0030: Numeric defaults

**Status:** Accepted (amended: table gains FunCaptcha / GeeTest v3 / GeeTest v4 rows per ADR-0070 — values at implementation, GeeTest/FunCaptcha class near reCAPTCHA cadence; `poll_delay` initial-wait column added; amended 2026-08-24: draft rows pinned for FunCaptcha / GeeTest v3/v4 / Turnstile from vendor-observed data (ADR-0074 session), pending thorough review — deferred item 15; ratified 2026-08-25: final token-kind rows and the source-hierarchy methodology settled, closing deferred item 15; amended 2026-08-31: image/text row split — text default `total_timeout` raised 30 s → 120 s (two live 2Captcha solves exceeded 30 s; 120 s anchored to 2Captcha's own `defaultTimeout`; image keeps 30 s))
**Date:** 2026-08-23, ratification 2026-08-25

## Context

Poll intervals, timeouts, retry counts, and backoff parameters need
ratified concrete values. Defaults differ by challenge kind (reCAPTCHA-class
tasks take far longer than image/text tasks; text is human-answered and
queue-bound, slower than OCR image tasks).

## Decision

The engine's per-kind default table:

| Parameter | reCAPTCHA v2/v3, hCaptcha | image | text | FunCaptcha, GeeTest v3/v4 | Turnstile |
|---|---|---|---|---|---|
| poll delay (before first poll) | 15 s | 5 s | 5 s | 10 s | 5 s |
| poll interval | 5 s | 2 s | 2 s | 3 s | 3 s |
| total_timeout (default) | 120 s | 30 s | 120 s | 180 s | 120 s |
| per-request HTTP timeout | 20 s | 20 s | 20 s | 20 s | 20 s |
| submit retry attempts (total) | 3 | 3 | 3 | 3 | 3 |
| backoff | full jitter, base 1 s, cap 30 s | same | same | same | same |

- **`poll_delay`** (amendment, from second-pass competitive analysis):
  the initial wait after submission before the first `getTaskResult`
  — first-useful-poll approximates typical solve time (competitors'
  operational data: image ~5 s, reCAPTCHA-class ~15-20 s). Applies
  always in `solve()`; in `wait(ticket)` only when the ticket is
  **fresh** (submitted less than one `poll_interval` ago — stale
  tickets poll immediately); never in `wait_ref`/`get_task_status`
  (reconstruction assumes the task may be mature). Counted within
  `total_timeout`.
- **Token-kind rows** (ratified 2026-08-25, closes deferred item 15):
  FunCaptcha 10/3/180, GeeTest v3/v4 10/3/180, Turnstile 5/3/120
  (delay/interval/total). Each knob follows the same source hierarchy as
  the original kinds:
  - **poll_delay** — first-useful-poll from competitor operational data:
    FunCaptcha/GeeTest typically solve in 10-30 s, Turnstile faster; the
    10/10/5 s drafts are kept.
  - **poll_interval** — provider-safe cadence: all four providers poll at
    1 s internally (CapMonster / Anti-Captcha / Capsolver SDKs); 2captcha
    legacy warns against <5 s; 3 s is the responsive, safe middle.
  - **total_timeout** — provider guidance *for the kind*, not
    universal-lib defaults: Anti-Captcha documents 300 s (Turnstile) and
    600 s (FunCaptcha/GeeTest) budgets; CapMonster tunes all three to
    80 s (its own-infra artifact, not a safe cross-provider default);
    universal wrappers (unicaps/anycaptcha) carry no per-kind data and
    fall back to 180-300 s. Final values take the defensible middle:
    180 s for FunCaptcha/GeeTest (Anti-Captcha documents up-to-10-minute
    solves; 120 s would false-timeout the slow tail) and 120 s for
    Turnstile (reCAPTCHA-class parity; typically fast).
- **Text row** (amended 2026-08-31): text split from the image/text
  row — 5/2/120 (delay/interval/total). Text is a human-answered question
  (`TextCaptchaTask`), queue-bound rather than OCR: two live 2Captcha
  solves exceeded the old 30 s budget (image solves at 30 s passed). The
  120 s total is anchored to 2Captcha's own `defaultTimeout=120`; the
  poll cadence stays at the image row's 5/2.
- Generic fallback gains `poll_delay` ~10 s.

- All values overridable at client level and per call via the None-merge
  chain (ADR-0043).
- The table is extended by custom adapters' `default_task_config`
  declarations with a generic fallback for adapters that declare none
  (ADR-0041).
- Kinds not in the table and not declared by the adapter receive the
  generic fallback (conservative: 120 s total / 5 s interval / 10 s delay).

## Rationale

- Numbers follow provider guidance (reCAPTCHA-class: poll ~5 s, solve up
  to ~2 min; images: fast, ~2 s polls, 30 s is ample; text: human-answered
  and queue-bound, 120 s anchored to 2Captcha's own `defaultTimeout`).
- Provider-recommended poll intervals avoid the too-fast-polling
  rate-limit trap.

## Alternatives considered

- **One default set for all kinds**: rejected; 120 s waits for images or
  30 s ceilings for reCAPTCHA would both be wrong.
- **Per-provider defaults**: rejected; timing is a property of the
  captcha kind, not the service.
