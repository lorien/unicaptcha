# ADR-0031: Field-surface specification level

**Status:** Accepted
**Date:** 2026-08-23

## Context

Per-provider challenge fields (2Captcha's `lang`, `hint`, `phrase`,
`numeric`, `math`, `min_len`, `max_len`, `case_sensitive`; CapMonster's
capability flags; enterprise/extra params) could be enumerated in design or
worked out during implementation against each provider's API reference.

## Decision

This knowledge base specifies the field surface at the **level of
principle**:

- universal fields live on kind bases (ADR-0048);
- each provider's classes carry exactly that provider's supported fields,
  no union pollution (ADR-0006);
- optional `proxy` on proxy-capable kinds (ADR-0012).

The exact per-provider field lists are deferred to implementation (see
deferred.md item 2), compiled against each provider's API reference and
covered by adapter tests.

## Rationale

- Owner decision ("enough"): provider field inventories churn; pinning
  them in design docs duplicates API references and ages instantly.
- The structural rules above make adding fields mechanical.

## Alternatives considered

- **Full field enumeration per provider in design**: rejected;
  duplication of vendor docs, stale on arrival.
