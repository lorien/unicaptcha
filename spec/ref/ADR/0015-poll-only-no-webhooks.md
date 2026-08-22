# ADR-0015: Poll-only solving, no webhooks

**Status:** Accepted
**Date:** 2026-08-23

## Context

All three services can push finished solutions to a registered callback URL
(2Captcha pingback, Anti-Captcha webhooks) as an alternative to polling.
Webhook mode implies server infrastructure from the caller and a receive
path in the library, and interacts with adapter/flow separation.

## Decision

v1 is **strictly poll-based**. No webhook/pingback registration, no
callback receipt. The engine's submit/await-result separation remains
internal structure only, not a webhook preparation.

Webhook mode stays deferred (deferred.md item 7); if added, it plugs into
the existing two-stage engine without rearchitecting.

## Rationale

- Owner decision for simplicity: polling covers the dominant use cases;
  webhook support would add surface, docs, and test burden with no v1
  demand.
- The two-stage internal design means the future addition is additive.

## Alternatives considered

- **Poll-based core, webhook-pluggable design from day one**: rejected;
  speculative structure for an unrequested mode.
- **Webhook-first**: rejected; requires caller-side servers, orthogonal to
  a client library's core job.
