# ADR-0028: No proxy validation

**Status:** Accepted (amended 2026-08-24: the two constructor fail-fast basics — non-empty `host`, `port` in 1..65535 — raise `InvalidConfigError`)
**Date:** 2026-08-23, amendment 2026-08-24

## Context

Proxies are structured objects (ADR-0036) with fail-fast basics (port
range, non-empty host). Beyond those constructor invariants, the library
could deeply validate/normalize proxy data locally (scheme reachability,
credential forms, canonical string building) or send values verbatim.

## Decision

No proxy validation or normalization beyond the dataclass constructor
basics. Values are sent verbatim to providers; provider-side complaints
surface through the normal error hierarchy.

## Rationale

- Owner decision: providers are the authority on what they accept; local
  reimplementations of their rules drift.
- The structured object form already prevents the classic typo class
  ("sock5", reversed host/port) without a validation engine.

## Alternatives considered

- **Local deep validation** (fail-fast on anything the provider would
  reject): rejected; duplicates provider rules, adds maintenance surface,
  risks false rejections.
