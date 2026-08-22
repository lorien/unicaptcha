# ADR-0037: Duplicate provider kinds forbidden

**Status:** Accepted
**Date:** 2026-08-23

## Context

The universal client registers providers in a `{kind: adapter}` registry.
Registering the same provider class twice (two accounts) would collide: one
registry slot, ambiguous string/class discriminators, and — less obviously —
ambiguous challenge dispatch (two adapters accept `TwoCaptcha*Challenge`:
which account pays?).

## Decision

Constructing a client with two providers sharing a `kind` raises
`ValueError` at construction time ("provider kind 'twocaptcha' registered
twice"). Multi-account setups are expressed as multiple clients (or
facades), optionally sharing one injected HTTP layer.

## Rationale

- Forbidding duplicates keeps every routing form statically unambiguous:
  challenge dispatch, string/class/instance discriminators.
- Matches the one-key-per-provider-instance scope decision (ADR-0014).
- The HTTP-layer injection seam makes multi-client setups cheap (one
  shared pool).

## Alternatives considered

- **Allow duplicates, require instance addressing**: rejected; ambiguity
  errors on string/class discriminators, challenge dispatch needs a
  selection policy (silent drift into deferred auto-routing territory).
- **Last-wins with warning**: rejected; silently discards the first
  account's configuration — data-losing magic.
