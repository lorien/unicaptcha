# ADR-0012: Proxy handling

**Status:** Accepted (worker-context fields `user_agent`/`cookies` follow the same challenge placement per ADR-0069)
**Date:** 2026-08-22

## Context

Providers differ in proxy support: Anti-Captcha and 2Captcha split task
types into with-proxy vs proxyless variants per kind (image/text tasks take
no proxy at all); CapMonster Cloud is entirely proxyless. A client-level
"one proxy for everything" is therefore conditional machinery.

## Decision

- **Challenge-level**: proxy-capable challenge classes carry an optional
  `proxy: Proxy | None` field (structured object: kind/host/port/optional
  auth, ADR-0036 types). One class per kind per provider; the adapter
  selects the provider's with-proxy vs proxyless task type based on the
  field's presence. Provider packages whose kinds accept no proxy simply
  have no such field (all of CapMonster).
- **Client-level default**: clients accept a default proxy applied only to
  proxy-capable challenges; a challenge's own proxy field wins when set.
  Applying a default to a proxy-incapable challenge is ignored with a
  WARNING log.
- **No validation/normalization machinery** beyond fail-fast basics
  (ADR-0028): values are sent verbatim; provider complaints surface through
  the normal error hierarchy.

## Rationale

- Presence/absence of a proxy must be encoded where the support lives: the
  challenge class. This mirrors provider task-type splits exactly.
- Optional field + adapter-side task-type selection avoids duplicating every
  class into `*Task`/`*TaskProxyless` pairs.
- Client-level default covers the common "route everything through one
  proxy" setup without per-challenge repetition.

## Alternatives considered

- **Two classes per kind** (mirroring provider task types): rejected;
  doubles the class count for no caller benefit.
- **Challenge-level only** (no client default): rejected by owner;
  per-challenge repetition is tedious for proxy-mandatory setups.
- **Local proxy string parsing/normalization**: rejected (ADR-0028).
