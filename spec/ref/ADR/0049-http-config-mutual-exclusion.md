# ADR-0049: HTTP config and injected client are mutually exclusive

**Status:** Accepted
**Date:** 2026-08-23

## Context

Callers can pass `http=HttpClientConfig(...)` (how to build) and/or an
injected httpx client (already built). Applying config onto an injected
client means mutating a caller-owned object (forbidden by the ownership
rule) or partially applying settings (false-expectation factory).

## Decision

- Passing **both** raises `InvalidConfigError` at client construction:
  "pass either `http` config or `http_client`, not both."
- Library-built path: config (or defaults) -> we construct, own, and
  close.
- Injected path: caller-owned; never closed by us, never mutated —
  including headers: the **User-Agent is attached per-request** on every
  outbound call (refining ADR-0026), so injected clients keep our
  identification without being touched.

## Rationale

- One honest behavior per path; no silent precedence, no partial
  application, no mutation of caller property.
- Fail-fast at construction keeps the mistake at the configuration line.

## Alternatives considered

- **Apply-what-we-can** (mutate settable attributes, warn on rest):
  rejected; violates ownership; partial application misleads.
- **Silently ignore config when client injected**: rejected; signals
  nothing.
