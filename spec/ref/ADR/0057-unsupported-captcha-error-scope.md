# ADR-0057: UnsupportedCaptchaError — client-side coverage gaps included

**Status:** Accepted (amends ADR-0009, ADR-0013, ADR-0053)
**Date:** 2026-08-23

## Context

ADR-0009 scoped `UnsupportedCaptchaError` to **server-side** task-type
rejection "only". But three settled mechanisms raise it client-side,
pre-flight, without any network traffic:

- the report-bad support matrix (ADR-0013: adapters raise it where the
  provider lacks coverage for the kind);
- `BaseAdapter`'s default-unsupported trio (ADR-0053:
  `report_bad_supported() -> False`, `build_report_bad` /
  `parse_report_bad` raise it);
- architecture.md §7 restates both.

The class's documented semantics contradicted the majority of its use
sites. The original "only" was written before the aux-op matrix and the
ABC defaults existed; ADR-0009's real insight — that client-side
*kind* gaps are impossible because no challenge class would exist —
does not extend to *operation* gaps: report-bad coverage is per
(provider, kind) while the challenge class exists and is solvable.

## Decision

`UnsupportedCaptchaError` means: **the provider does not support this
operation for this captcha kind.** Both sources raise it:

- **server-side**: provider rejects a submitted task type (plan,
  account, dropped support);
- **client-side, pre-flight**: adapter's support matrix says the
  operation is not covered (e.g. report-bad on a kind the provider
  never accepts reports for); no network traffic occurs.

It is never raised for wrong-provider routing (that is `TypeError`,
ADR-0045) nor for unknown task ids (that is `TaskStatus.UNKNOWN`,
ADR-0050).

## Rationale

- One exception class per caller-actionable meaning; splitting
  server/client variants would fork the hierarchy for a distinction
  the caller cannot act on differently (both mean "don't retry this
  operation with this provider").
- Pre-flight raising is strictly better than discovering the gap after
  a round trip: fail fast, no traffic, message names the kind and the
  operation.

## Alternatives considered

- **Split classes** (`UnsupportedCaptchaError` +
  `ReportNotSupportedError`): rejected; two leaves for one meaning,
  catch complexity for nothing.
- **`NotImplementedError`**: rejected; a builtin reserved for
  unimplemented code paths, not a domain answer.
- **Silent no-op on unsupported report-bad** (return False): rejected;
  hides caller mistakes, contradicts operations-raise (ADR-0050
  principle applied to aux ops).
