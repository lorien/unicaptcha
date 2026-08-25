# ADR-0005: Universal multi-provider client

**Status:** Accepted (amended by ADR-0052: the registration argument is `adapters=`, accepting adapter instances)
**Date:** 2026-08-22

## Context

The universal client must choose between binding to exactly one provider
(one client = one credential, rejects foreign challenges) or holding several
providers and dispatching per challenge class. The two-tier API design
(universal client + provider facades) interacts with this choice: facades
exist precisely to give per-provider ergonomics.

## Decision

The universal client (`Solver` / `AsyncSolver`, naming per
ADR-0062) accepts a
**list of adapters**, each with its own credentials:

```python
client = Solver(adapters=[two_captcha, anti_captcha])
client.solve(TwoCaptchaImageChallenge(body=b"..."))   # routes to 2Captcha
client.solve(AntiCaptchaRecaptchaV2Challenge(...))    # routes to Anti-Captcha
```

- Dispatch is **type-based**: for concrete challenge classes,
  constructing the challenge is the provider
  choice. There is deliberately no provider-agnostic
  `solve_image(...)` method on the universal client, because no
  honest universal parameter surface exists (providers differ in
  supported fields) and provider selection would become library
  magic. (Amended by ADR-0064: kind-base challenges are now
  instantiable and solvable via `solve(ImageChallenge(...),
  provider=None | "name")` — universal fields only, explicit or
  random provider choice; the method-name objection is unaffected.)
- A challenge whose provider is not registered raises `TypeError`
  pre-flight.
- No automatic provider selection, failover, or load balancing (deferred,
  see deferred.md item 4).

## Rationale

- Multi-provider clients are a primary use case (fallback, quota
  splitting); requiring one client per provider would defeat "universal".
- Type-based dispatch is explicit, statically checkable, and requires zero
  runtime routing decisions: the challenge class identifies the adapter.
- Kept honest by facades: per-provider ergonomics live in the facade tier
  (ADR-0007), not by leaking provider-specific methods into the universal
  client.

## Alternatives considered

- **Single-provider client**: rejected; "one object per provider" fragments
  the primary use case.
- **Universal convenience methods with a provider-argument**: rejected;
  union-polluted parameters and forced selection semantics.
- **Automatic routing (cheapest/failover)**: deferred as an additive layer.
