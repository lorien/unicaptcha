# ADR-0039: Logging taxonomy

**Status:** Accepted
**Date:** 2026-08-23

## Context

Stdlib logging under the `unicaptcha` namespace was settled early; the
level-by-level content contract was not. Solution tokens are
secrets-adjacent; API keys must never appear; errors are exceptions, not
log lines.

## Decision

| Level | Content | Never contains |
|---|---|---|
| DEBUG | full request lifecycle: HTTP method/URL, status, raw response bytes, poll iterations, retry decisions with reasons, unknown response fields (ADR-0040) | API keys (scrubbed) |
| INFO | task submitted (provider, task_id), task solved (task_id, elapsed), client opened/closed | solution tokens, keys, bodies |
| WARNING | retryable failures, proxy ignored on proxy-incapable kind, registry eviction (ADR-0038), awaitable handler result discarded (ADR-0018) | |
| ERROR | nothing — errors are exceptions; callers decide how to log caught exceptions | |

Additional rules:

- **Solution tokens never appear at any level** — they are the product;
  leaking them into logs is a data leak.
- Key scrubbing is targeted (we construct every payload; keys occupy known
  positions), not regex-over-everything.
- One flat `unicaptcha` logger (ADR-0018); client identity via optional
  `name` as message context.

## Rationale

- "Nothing at ERROR" avoids double-reporting: the library raises; the
  application logs.
- DEBUG carries everything an integrator needs to reconstruct a provider
  conversation, minus secrets.

## Alternatives considered

- **ERROR-level library logs on failures**: rejected; double-reporting,
  surprise console output.
- **Tokens at DEBUG**: rejected; single-use or not, logs outlive solves
  and aggregate.
