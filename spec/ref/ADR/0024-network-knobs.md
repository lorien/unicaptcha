# ADR-0024: Network knobs

**Status:** Accepted (amended 2026-08-23: TLS omitted → injection-only; HTTP/2 rejected; per-request User-Agent refined in ADR-0049's amendment note)
**Date:** 2026-08-22

## Context

Clients need network-level configurability: per-request timeouts, pool
limits, custom base URLs (mirrors, self-hosted, test doubles), TLS
customization (corporate CAs), HTTP/2, and injection of pre-configured
httpx clients. Each knob costs config surface and documentation.

## Decision

Exposed on the library (via `HttpClientConfig` or constructor):

1. **Per-request HTTP timeout** (`timeout`, default 20 s) — independent of
   the solve budget.
2. **Connection pool limits** (`max_connections`,
   `max_keepalive_connections`) — passthrough to httpx pool defaults when
   None.
3. **Per-provider `base_url` override** — RuCaptcha-style mirrors,
   integration-test doubles.
4. **Injectable httpx client** — the escape hatch subsuming exotic needs
   (custom transports, TLS contexts, event hooks). Ownership: injected
   clients are caller-owned, never closed by us, never mutated.
   Mutually exclusive with `HttpClientConfig` (ADR-0049).

Not exposed:

- **TLS knobs** (`verify`, `cert`): custom TLS means constructing your own
  httpx client and injecting it. `HttpClientConfig` stays behavior-only;
  no officially supported `verify=False` footgun.
- **HTTP/2**: no `httpx[http2]` dependency; poll-based JSON APIs gain
  nothing measurable from it.

**User-Agent**: `unicaptcha/<version> (+https://github.com/lorien/unicaptcha)`
sent **per-request** by the HTTP layer (ADR-0026, ADR-0049) — never by
mutating any client's default headers, so injected clients are untouched.
Overridable via constructor flat kwarg.

## Rationale

- Every exposed knob is one we must test and keep; injection covers the
  long tail better than a knob-per-feature.
- Pool limits and base URLs have concrete, common uses; TLS/HTTP/2 do not
  at v1.

## Alternatives considered

- **`verify`/`cert` passthrough in HttpClientConfig**: rejected; one-flag
  insecure mode officially offered, config noise for a corporate-only
  case the injection hatch already serves.
- **HTTP/2 extra**: rejected; negligible gain for poll-based traffic.
