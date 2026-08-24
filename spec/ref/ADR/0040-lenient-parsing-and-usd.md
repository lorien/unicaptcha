# ADR-0040: Lenient parsing and USD-pinned balance

**Status:** Accepted (currency verification note added 2026-08-23; `EmptySolutionError` amendment added 2026-08-23)
**Date:** 2026-08-23

## Context

Providers drift: responses gain unknown fields (new features) and drop
optional ones. Strict parsing breaks users on harmless drift; fully silent
parsing hides it. Separately, `get_balance()` needs a currency contract —
all three services bill in USD.

## Decision

- **Lenient parsing with visibility**: parse only known fields; unknown
  fields are ignored **and logged at DEBUG** (one line per unknown field,
  provider named). Missing optional fields become `None`. Provider drift
  becomes visible during debugging without breaking anyone.
- **Malformed responses are not drift**: HTTP 200 with an unparseable body
  or wrong-shape JSON raises `ProviderError` with `raw_response` bytes
  preserved and the parse failure as `__cause__` (ADR-0009).
- **Empty solutions are their own diagnosis** (amendment): a "solved"
  response whose solution payload is empty (empty token/text) raises
  **`EmptySolutionError`**, a subclass of `ProviderError`
  (`ErrorKind.EMPTY_SOLUTION`, 13th value), `raw_response` preserved;
  detected in the adapter's parse path. Rationale: empty answers are
  typically transient worker failures — callers may retry or reroute —
  whereas generic garbage means protocol drift where retrying will not
  help. Distinct remediation earns a distinct type (the
  `ServiceBusyError` precedent, ADR-0059 amendment).
- **Balance is USD-pinned**: `get_balance() -> Decimal`, documented as
  always USD. No currency field, no conversion.
- **Verification note (implementation-time)**: confirm each provider's
  balance-field currency, including 2Captcha — accounts may be
  currency-scoped by registration (anycaptcha reports 2Captcha
  balances as RUB). If any provider returns non-USD: convert nothing,
  document that provider's actual currency, and revisit the pin
  (candidate shapes: per-provider documented currency, or
  `tuple[Decimal, str]`).

## Rationale

- Unknown-but-well-formed is not an error; unparseable is. The DEBUG line
  closes the observability gap that silent ignoring creates.
- Honesty over false generality on currency: inventing a currency field
  for a world where all three providers report USD would be speculative.

## Alternatives considered

- **Strict parsing (reject unknowns)**: rejected; provider-side feature
  additions would break clients mid-rollout.
- **Fully silent ignoring**: rejected; drift invisible until symptoms.
- **Currency-agnostic balance objects**: rejected; speculative
  generality.
- **Plain `ProviderError` for empty solutions** (amendment
  alternative): rejected; empty answers are actionable (retry/reroute)
  unlike generic garbage.
- **ErrorKind without a class** (`ProviderError(kind=EMPTY_SOLUTION)`):
  rejected; breaks the 1:1 class-per-kind symmetry every other value
  keeps.
