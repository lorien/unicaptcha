# ADR-0068: report_good_result

**Status:** Accepted (amends ADR-0013, ADR-0053)
**Date:** 2026-08-23

## Context

Competitive analysis (unicaps/anycaptcha, session 2026-08-23) surfaced
an asymmetry: we ship `report_bad_result` but no positive counterpart.
Their code shows both reports are real provider operations with a
genuinely partial support matrix: 2Captcha-family implements both
(`res.php` `reportgood`/`reportbad`); Anti-Captcha keeps a
`ReportGoodRequest` that raises "not supported" at prepare time, and
its report-bad covers only image + reCAPTCHA. Positive reports are
not mere politeness — providers that accept them use the signal for
worker quality routing (2Captcha docs).

## Decision

- **`report_good_result(task)`** on both tiers, exact mirror of
  `report_bad_result` routing (ADR-0013): universal tier takes
  `TaskRef`; facades take `TaskRef | int` (implicit provider).
- Returns **`bool`** — provider accepted the report or not (symmetric
  with `parse_report_*`; zero cost for callers who ignore it).
- Unsupported coverage raises `UnsupportedCaptchaError` pre-flight,
  no network traffic (ADR-0057's both-sides scope applies unchanged);
  wrong provider -> pre-flight `TypeError` (ADR-0045); same aux retry
  policy as submission (ADR-0011).
- **Adapter SDK pairs** — the default-unsupported trio on
  `BaseAdapter` (ADR-0053) becomes symmetric pairs; good-side
  defaults are unsupported exactly like bad-side:

| Bad (existing) | Good (new) |
|---|---|
| `report_bad_supported(challenge_type) -> bool` | `report_good_supported(challenge_type) -> bool` |
| `build_report_bad(task) -> dict` | `build_report_good(task) -> dict` |
| `parse_report_bad(raw) -> bool` | `parse_report_good(raw) -> bool` |

  Defaults: `*_supported -> False`; build/parse raise
  `UnsupportedCaptchaError`. Shipped adapters override per the real
  per-provider/per-kind matrix.
- **Naming**: `report_good_result` — adjective-first, the consistent
  twin of `report_bad_result`.
- Documented at the method: positive reports feed worker quality
  routing on providers that support them.

## Rationale

- Symmetry: a support matrix that models "provider lacks coverage"
  for bad reports models it identically for good ones; the ABC
  default-unsupported pattern already exists — the addition is
  mechanical, zero new concepts.
- `bool` return matches the parse layer's contract and keeps the
  surface honest (the provider does answer accept/reject).

## Alternatives considered

- **No method** (status quo): rejected; the asymmetry is an API gap,
  not a scope guard.
- **`report_result_good` word order**: rejected; breaks the
  adjective-first family (`report_bad_result`).
- **Combined `report(result, good: bool)`**: rejected; boolean-mode
  flag selects two different provider operations behind one name.
- **SolveResult-object method (`result.report_good()`)**: rejected; engine
  reference inside frozen data (same rejection as ADR-0067's handle
  methods).
