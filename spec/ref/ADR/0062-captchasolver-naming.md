# ADR-0062: Universal client naming — `CaptchaSolver` / `AsyncCaptchaSolver`

**Status:** Accepted (supersedes the class-name decision of ADR-0054; amends ADR-0036)
**Date:** 2026-08-23

## Context

ADR-0054 renamed the universal client to `MultiClient` /
`AsyncMultiClient` (from `UnicaptchaClient`, which filled the
`<Provider>Client` slot with the library's own name and read as a
facade for a nonexistent "Unicaptcha" service).

Post-commit review found `MultiClient` still suboptimal:

- the tier distinction from facades is prefix-only
  (`MultiClient` vs `TwoCaptchaClient` share the `Client` suffix;
  "Multi" is ambiguous — multi-what? kinds? accounts?);
- importing a generic-sounding `*Client` at root carries a residual
  collision risk with other SDKs' `Client` exports — the same
  objection that sank bare `Client`;
- the name describes inventory (holds many providers), not the job
  from the caller's chair.

Two further candidates were explored: bare `Solver` (job-naming,
lexical distinction — but unqualified: "solver of what?", ecosystem
collision risk) and `CaptchaSolver` (job + domain).

## Decision

- The universal client classes are **`CaptchaSolver`** and
  **`AsyncCaptchaSolver`**.
- Tier naming becomes **lexical**: `CaptchaSolver` (universal,
  holds many providers, dispatches by challenge class) vs
  `<Provider>Client` (facade, static provider, convenience methods).
- The `Client` suffix rule (ADR-0036) is **scoped to facades**; the
  universal tier does not end in `Client`.
- `adapters=` registration kwarg unchanged (ADR-0052); facade
  constructor parity unchanged (ADR-0061).
- Prose continues to say "universal client" as the descriptive tier
  term; only class names change.

## Rationale

- Job + domain in one self-contained name: what it does (solves) and
  over what (captchas). At import and annotation sites
  (`def get_past(solver: CaptchaSolver, ...)`) it teaches role and
  domain without requiring the README.
- The domain echo (`unicaptcha.CaptchaSolver`) is redundant-true, not
  false: the package is universal-captcha, the class is the captcha
  solver. Unlike `UnicaptchaClient`'s vendor stutter, it asserts
  nothing false.
- Lexical distinction from facades is categorical — different word
  classes cannot be confused at a skim, where prefix/suffix pairs can.
- Consistent with the session's naming taste: specific over generic
  (`adapters=`, `provider` attribute, rejection of bare `Client`).
- Known costs, accepted: aux ops (`get_balance`, `abandoned_tasks`,
  `close`) strain "solver" mildly; providers self-market as "captcha
  solvers" (tolerable — nothing in-code shares the name; from the
  caller's chair the object does exactly this).

## Alternatives considered

- **`MultiClient` / `AsyncMultiClient`**: superseded by this ADR;
  prefix-only tier distinction, inventory-not-job naming, residual
  generic-`Client` collision.
- **`Solver` / `AsyncSolver`**: rejected as unqualified — "solver of
  what?"; mild ecosystem collision risk; everything else it does,
  `CaptchaSolver` does with the domain attached.
- **The full 0054 candidate set** (`Client`, `UnicaptchaClient`,
  `Unicaptcha`, `Hub`, `UniversalClient`, `Gate`, `Master`, `Worker`,
  `Composer`, `Dispatcher`, ...): see ADR-0054; their rejection
  reasons are unaffected by this refinement.
