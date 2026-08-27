# ADR-0026: User-Agent identification and repository URL

**Status:** Accepted (amended: per-request attachment, see ADR-0049)
**Date:** 2026-08-23

## Context

Requests may identify the calling library to providers. A custom
User-Agent aids provider-side debugging and is requested by some services.
Mutating an injected httpx client's default headers would violate the
ownership rule.

## Decision

- Default User-Agent: `unicaptcha/<version> (+https://github.com/lorien/unicaptcha)`.
- Sent **with each request** by the HTTP layer; never set as client-level
  default headers; injected caller clients are never mutated.
- Overridable via a flat constructor kwarg (`user_agent`).
- Repository URL fixed as `https://github.com/lorien/unicaptcha` and used
  in README, pyproject metadata, and the User-Agent.

## Rationale

- Provider-visible identification costs nothing and helps when providers
  debug customer issues.
- Per-request attachment keeps one uniform behavior across library-built
  and injected clients without mutation.

## Alternatives considered

- **No custom UA**: rejected; identification is free value.
- **UA via client default headers**: rejected; requires mutating injected
  clients or losing the UA on them.
