# ADR-0007: Provider facades as peers over a shared engine

**Status:** Accepted (supersedes the original "facades compose a universal client" decision)
**Date:** 2026-08-22, restructured 2026-08-23

## Context

Provider facades (`TwoCaptchaClient`, ...) add convenience methods mirroring
exactly what each provider supports. The original composition decision had
each facade construct/wrap its own universal client instance. LSP analysis
and owner review exposed this as over-engineered: a facade knows its
provider statically and needs no dispatch machinery; wrapping a universal
client inside facades creates nesting questions (shared pools, ownership,
validation of "facade over a client lacking its provider").

## Decision

Facades and the universal client are **peers**, not nested:

```
Solver (registry + dispatch)           TwoCaptchaClient (facade)
                +--------------------------------------+
                |            TaskEngine                |
                |  adapters (pure)                      |
                |  HTTP layer (injection seam)          |
                +--------------------------------------+
```

- Both tiers delegate to the same internal **TaskEngine**
  (submit/poll/retry/timeout/events/registry/aux ops).
- The facade creates its adapter and the engine directly; no universal
  client appears in its object graph.
- Resource sharing happens at the **HTTP layer**: `TwoCaptchaClient(...,
  http_client=my_http)` and `Solver(..., http_client=my_http)`
  inject the same object at the layer where the resource actually lives.
- Facade method surface: `solve_image`, `solve_text`, `solve_recaptcha_v2`,
  `solve_recaptcha_v3`, `solve_hcaptcha`, plus aux ops with identical names
  to the universal client. Facade methods carry full parameter parity
  (`time=`, `retry=`, `on_event=`, ADR-0051).
- The earlier inheritance option was rejected on LSP grounds: a
  `TwoCaptchaClient(Client)` restricting the parent's multi-provider
  contract strengthens preconditions, the classic LSP violation.

## Rationale

- Facades need no dispatch; forcing them through a universal client added
  machinery without capability.
- One solve loop written once (engine), used by both tiers; adapters stay
  pure and shared.
- HTTP-layer injection is the single seam where external resources enter;
  ownership rules (ADR-0024) apply uniformly.

## Alternatives considered

- **Facades composing a universal client** (options "build own" /
  "wrap caller's" / "either"): superseded; produced nesting and ownership
  contortions, and "three facades = three hidden clients/pools".
- **Inheritance** (`TwoCaptchaClient(Client)`): rejected; LSP violation by
  narrowing, and silently ambiguous inherited aux ops.
- **No facades; convenience functions on provider objects**: rejected;
  facade objects match the two-tier API contract the owner specified.
