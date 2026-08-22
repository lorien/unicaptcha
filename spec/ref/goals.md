# Goals

## Motivation

Anti-captcha services (2Captcha, Anti-Captcha, CapMonster Cloud, ...) expose
similar but not identical JSON APIs for solving CAPTCHAs. Applications that use
them typically hard-code one provider's client library, accept its API shape,
and face a rewrite when switching providers or adding a second one as fallback.

unicaptcha provides one universal, strictly-typed interface over multiple
providers, with per-provider specificity preserved where services genuinely
differ, instead of a lossy lowest-common-denominator abstraction.

## Goals

1. Universal interface: one client API operating across all supported providers.
2. Provider fidelity: per-provider challenge classes and solution types expose
   exactly what each service supports; no union-polluted parameter bags.
3. First-class typing: full annotations, py.typed, mypy strict + pyright strict,
   generic Result types with non-optional solutions.
4. Dual execution models: async-native implementation plus a blocking sync
   implementation as peers (no wrapper magic in either direction).
5. Predictable failure semantics: one exception hierarchy with normalized
   ErrorKind, raw provider bytes preserved, status queries that answer rather
   than throw.
6. Extensibility: a public adapter SDK allowing third-party providers from day
   one.
7. Operational honesty: total-time budgets, safe close semantics, abandoned-task
   accounting, no secret leakage into logs or reprs.

## Non-goals (v1)

- Automatic provider selection, failover, load balancing, or routing policies.
- Client-side rate limiting or concurrency caps.
- API-key rotation or multi-account management per provider kind.
- Webhook/pingback solve mode; solving is strictly poll-based.
- Browser automation, CAPTCHA detection, or page scraping.
- A fake/test double module for downstream users (unicaptcha.testing).
- Per-provider billing dashboards or usage statistics on the client.

See [deferred.md](deferred.md) for the canonical list with rationale.

## Target users

- Developers of automation, testing, and scraping tooling who need CAPTCHA
  solving as one component of a larger system.
- Library authors who want to accept "any anti-captcha service" without
  depending on a specific vendor SDK.
- Teams that must switch providers or run several simultaneously (cost, quota,
  or availability reasons) behind one code path.

## v1 scope

- Providers: 2Captcha (modern JSON API), Anti-Captcha, CapMonster Cloud.
- CAPTCHA kinds: image, text, reCAPTCHA v2 (checkbox + invisible),
  reCAPTCHA v3, hCaptcha.
- Python: 3.11+ (all alive versions; see ADR-0004).
- Runtime dependencies: httpx only.
- Distribution: PyPI package `unicaptcha`; MIT license.
- Documentation: README only for v1; this spec directory is the internal
  design record.

## Status

Highly experimental. Pre-1.0. No public API stability is promised, even for
the documented surface. The public/internal boundary (ADR-0041) communicates
intent, not commitment.
