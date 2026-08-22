# ADR-0001: Supported providers

**Status:** Accepted
**Date:** 2026-08-22

## Context

The library aims to be a universal interface over anti-captcha services. The
market has many services with similar but not identical JSON APIs: 2Captcha
(and its mirror RuCaptcha), Anti-Captcha, CapMonster Cloud, DeathByCaptcha,
NextCaptcha, and others. Supporting everything at once dilutes v1 quality.

## Decision

Support exactly three providers in v1:

| Provider | kind | Default base URL |
|---|---|---|
| 2Captcha | `twocaptcha` | `https://api.2captcha.com` |
| Anti-Captcha | `anti-captcha` | `https://api.anti-captcha.com` |
| CapMonster Cloud | `capmonster` | `https://api.capmonster.cloud` |

For 2Captcha, target the **modern JSON API** (`createTask`/`getTaskResult`),
not the legacy `in.php`/`res.php` text protocol. RuCaptcha and other
2Captcha-protocol mirrors work by overriding the 2Captcha adapter's
`base_url`. Self-hosted CapMonster (the legacy desktop product) is out of
scope; only CapMonster Cloud's API is supported.

## Rationale

- The three chosen services are the most widely used and cover the spectrum:
  2Captcha (largest, most features), Anti-Captcha (API-clean reference
  implementation), CapMonster Cloud (cheapest, proxyless-only).
- All three speak a `createTask`/`getTaskResult`-shaped JSON protocol; one
  adapter architecture covers them uniformly.
- The modern 2Captcha API shares the response shape family with the other
  two; the legacy text protocol would require a second protocol stack for
  one provider.
- Fewer providers in v1 means the universal abstraction is proven on real
  diversity instead of guessed at.

## Alternatives considered

- **All major services (2Captcha, Anti-Captcha, CapMonster, DeathByCaptcha,
  RuCaptcha as separate adapter, CaptchaSolver, NextCaptcha, ...)**: rejected
  for v1; quality over coverage.
- **Start with a single provider**: rejected; a "universal" library with one
  provider validates nothing.
- **Legacy 2Captcha protocol**: rejected; pipe-delimited text responses,
  weaker error semantics, and no parity with the other two services.
