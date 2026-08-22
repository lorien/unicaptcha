# ADR-0040: Lenient parsing and USD-pinned balance

**Status:** Accepted
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
- **Balance is USD-pinned**: `get_balance() -> Decimal`, documented as
  always USD. No currency field, no conversion.

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
