# ADR-0051: Facade parameter parity

**Status:** Accepted (constructor parity per ADR-0061)
**Date:** 2026-08-23

## Context

Facade convenience methods were designed as mirrors of challenge fields.
The universal `solve()` additionally accepts `solve=`, `retry=`,
`on_event=`. Do facades? The peers architecture (ADR-0007) makes this
load-bearing: facades compose their own engine and have no underlying
universal client to "drop down to" for tuning.

## Decision

Full parity: every facade convenience method accepts `solve=SolveConfig`,
`retry=RetryConfig`, and `on_event=handler` as keyword-only parameters
alongside challenge fields, with the same merge/override semantics as the
universal `solve()` (ADR-0043, ADR-0044).

```python
tc.solve_image(body=b"...", solve=SolveConfig(total_timeout=60),
              on_event=handler)
```

## Rationale

- Necessary for completeness: without parity, a facade user with a slow
  proxy or a custom handler has no path to tune the call — the tier
  system would leak, and the only fix would be inventing a generic
  passthrough method (new surface).
- Keyword-only optional parameters cost nothing at call sites that
  ignore them; one rule ("every solving call takes the same knobs").

## Alternatives considered

- **Challenge fields only**: rejected; impossible to tune without
  bypassing the facade (which cannot exist under the peers
  architecture).
- **Parity for `on_event` only, configs client-level only**: rejected;
  arbitrary split — one-off timeouts are as legitimate as one-off
  handlers.
