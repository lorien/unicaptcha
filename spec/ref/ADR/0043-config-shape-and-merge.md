# ADR-0043: Config shape and merge semantics

**Status:** Accepted (amended: `poll_delay` added to TimeConfig per the ADR-0030 amendment; renamed 2026-08-24: `SolveConfig` → `TimeConfig`, `solve=` per-call kwarg → `time=` per the task-centric vocabulary)
**Date:** 2026-08-23, amendment 2026-08-24

## Context

Knobs proliferated (timeouts, retries, poll interval, pool limits, ...).
Flat-kwarg constructors risk 12-parameter signatures; grouping needs
override semantics between client-level and per-call configs. Two fields
(`total_timeout`, `poll_interval`) have per-challenge-kind defaults, but a
config object is constructed before any challenge exists.

## Decision

**Shape** — three frozen config types, grouped by concern; identity
scalars stay flat constructor kwargs (`name`, `user_agent`,
`abandoned_registry_limit`):

```python
NetworkConfig(timeout, max_connections, max_keepalive_connections)
TimeConfig(total_timeout, poll_interval, poll_delay)
RetryConfig(max_attempts, backoff_base, backoff_cap)
```

Accepted at client construction and per call (`solve(challenge, time=...,
retry=...)`), identical on facades (ADR-0051).

**None-rule** — every field in all three types is `X | None = None`.
`None` means "unspecified": not a value, an absence to be filled later.
One uniform rule across all config types (owner decision over
None-ability only for the two per-kind fields).

**Resolution chain** — resolved by the engine at solve time, field-wise:

```
per-call explicit value -> client-level explicit value -> per-kind default
table (ADR-0030; adapter-declared for custom kinds, generic fallback)
```

**Field-wise merge** (owner decision): a per-call config **inherits** unset
fields from the client config. It never discards client-level values —
the all-or-nothing alternative would silently reset a client's
`total_timeout` because an unrelated per-call field was set.

## Rationale

- Grouped configs keep signatures at 3-4 arguments, are reusable across
  clients, and match the frozen-dataclass model vocabulary.
- The None-sentinel solves "one slot, per-kind defaults" cleanly and
  uniformly.
- Field-wise merge is least-surprise: independent knobs combine
  independently.

## Alternatives considered

- **Flat kwargs everywhere**: rejected; name-collision-prone 12-arg
  signatures.
- **All-or-nothing per-call replacement**: rejected; silently discards
  explicitly-set client values (inconsistent with `on_event`-style
  override? — no: `on_event` is a single value with no fields to merge;
  the situations are not analogous).
- **None-ability only for per-kind fields**: rejected; two mental models
  instead of one uniform rule.
