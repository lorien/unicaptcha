# ADR-0071: Capsolver as the fourth shipped provider

**Status:** Accepted (amends ADR-0001)
**Date:** 2026-08-23

## Context

Provider-gap review (session 2026-08-23, from unicaps/anycaptcha
inventories plus live docs verification). The market splits three
ways:

1. **JSON-family providers** — `createTask`/`getTaskResult`
   protocols like our three. Capsolver is the significant one we
   lack: modern, growing, good GeeTest v4/FunCaptcha coverage
   (strengthening the ADR-0070 kind grid), verified to speak the
   JSON family (competitor code drives it with the same methods).
2. **2Captcha mirrors** — RuCaptcha and friends. Live-docs check
   (2026-08-23): RuCaptcha is the same operator as 2Captcha
   ("international version" cross-link) and its **API v2 (JSON) is
   complete and current**, versioned in lockstep — so it needs no
   shipped adapter, just `base_url` on `TwoCaptchaAdapter`. Smaller
   mirrors (azcaptcha, cap.guru, cptch.net, sctg.xyz, multibot)
   have unreachable/unverified docs; their JSON-API status is
   unknown.
3. **Other-protocol providers** — DeathByCaptcha (own REST,
   authtoken auth). A second protocol family for a declining
   service.

## Decision

- **Capsolver ships in v1** as the fourth provider:
  `CapsolverAdapter`, facades `CapsolverClient` /
  `AsyncCapsolverClient`, package `unicaptcha.providers.capsolver`.

| Provider | kind | Default base URL |
|---|---|---|
| 2Captcha | `twocaptcha` | `https://api.2captcha.com` |
| Anti-Captcha | `anti-captcha` | `https://api.anti-captcha.com` |
| CapMonster Cloud | `capmonster` | `https://api.capmonster.cloud` |
| Capsolver | `capsolver` | `https://api.capsolver.com` |

- Kind coverage = adapter's `challenges` declaration; per-kind field
  matrices ride deferred item 2 like every provider.
- **Mirrors stay `base_url` territory** — no shipped mirror
  adapters. RuCaptcha is verified-working via API v2; smaller
  mirrors need per-service verification before use (documented
  caveat), and third-party adapters may cover them meanwhile.
- **Deferred providers by name** (deferred.md): DeathByCaptcha,
  azcaptcha, cap.guru, cptch.net, sctg.xyz, multibot — with
  reasons.

## Rationale

- Capsolver is the only verified-cheap addition: one adapter in the
  protocol family we already drive; closes the "no fourth modern
  provider" gap competitors exploit.
- Shipping six near-identical mirror adapters would be maintenance
  mass, not value — the URL override and the public SDK cover the
  long tail better.
- Verified-not-assumed: the RuCaptcha API v2 check upgraded the
  mirror story from "should work" to documented fact.

## Alternatives considered

- **Stay at three providers**: rejected; Capsolver is cheap and
  demand-real.
- **Add several (Capsolver + mirrors)**: rejected; mirrors are
  URL-swaps or unverified, never worth shipped adapters.
- **Legacy 2Captcha protocol support** (to serve older mirrors):
  rejected; second protocol stack, pipe-delimited text, weaker
  error semantics (ADR-0001's original reasoning stands).
- **DeathByCaptcha**: rejected; other-protocol-family cost for a
  declining service.
