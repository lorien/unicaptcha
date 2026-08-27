# ADR-0076: Per-provider challenge field surface

**Status:** Accepted (closes deferred item 2; amends ADR-0006, ADR-0031,
ADR-0069 field-scope claims: the concrete per-provider field lists are
hereby pinned in architecture.md §2)
**Date:** 2026-08-25

## Context

Deferred item 2 postponed the exact per-provider challenge field lists —
which fields each provider's challenge classes carry beyond the universal
kind-base fields, including the worker-context surface (ADR-0069). The
typing policy was settled (provider extras as primitives; StrEnum
promotion later), as was Anti-Captcha's IP-only proxy rule. The lists
themselves were to be "worked out during implementation against each
provider's API reference." Before implementing the four adapters, they are
now pinned against the primary sources collected in `var/analysis-*.md`
(official SDKs) and live provider API docs (2Captcha modern JSON API,
Anti-Captcha).

## Decision

The full surface lives in architecture.md §2 ("Provider-specific challenge
field surface") — one table per provider. Boundary rules settled here:

### Coverage matrix

| Kind | 2Captcha | Anti-Captcha | CapMonster | Capsolver |
|---|---|---|---|---|
| image | ✓ | ✓ | ✓ | ✓ |
| text | ✓ | ✓ (API `TextCaptchaTask`; SDK lacks it) | ✗ | ✗ |
| reCAPTCHA v2 | ✓ | ✓ | ✓ | ✓ |
| reCAPTCHA v3 | ✓ | ✓ (proxyless) | ✓ (proxyless) | ✓ (proxyless) |
| hCaptcha | ✓ | ✓ | ✓ | ✓ |
| FunCaptcha | ✓ | ✓ | ✓ | ✓ |
| GeeTest v3 | ✓ | ✓ | ✓ | ✓ |
| GeeTest v4 | ✓ | ✓ | ✓ | ✓ (amended 2026-08-27: live docs document `captchaId`/`riskType`; the SDK-only exclusion was stale) |
| Turnstile | ✓ | ✓ | ✓ | ✓ (`AntiCloudflareTask`) |

- **Text is 2-provider**: CapMonster and Capsolver ship no text task in
  their APIs; the kind stays universal but only two adapters register it.
- **Capsolver GeeTest v4 excluded**: ~~the official Capsolver SDK ships
  GeeTest v3 only (no `captchaId` params). Thin coverage is acceptable
  (ADR-0070); the adapter registers GeeTest v3 only~~ **amended
  2026-08-27 (task 14)**: current Capsolver docs document GeeTest v4
  (`captchaId` + `riskType` on `GeeTestTask[ProxyLess]`); the exclusion
  was SDK-stale (2024 clone). Capsolver now ships GeeTest v3 **and** v4.
- **reCAPTCHA v3 is proxyless-only on all four providers** (amended
  2026-08-27 after live-docs verification: 2Captcha documents
  `RecaptchaV3TaskProxyless` only — the earlier "2Captcha additionally
  exposes a proxy variant" claim was unverified and wrong). Capsolver
  additionally exposes **no v3-enterprise task type**; its v3 challenge
  rejects `is_enterprise` (task-14).
- **Capsolver Turnstile** (amended 2026-08-27, task 14): the task type is
  **`AntiTurnstileTaskProxyLess`**, proxyless-only, and the provider
  ignores `userAgent`; `AntiCloudflareTask` is the separate
  Cloudflare-challenge task, not Turnstile. `chl_page_data` is not
  supported (only `metadata.action`/`metadata.cdata`).

### Field rules

- **Universal→wire mapping** follows the convention `sitekey`→`websiteKey`,
  `pageurl`→`websiteURL` unless the wire name differs (per-row notes in the
  tables). Provider extras are keyword-only primitives (ADR-0066).
- **Proxy surface** (ADR-0012 honored): CapMonster challenges carry **no**
  proxy field (proxyless service); 2Captcha/Anti-Captcha/Capsolver carry
  the optional `proxy` field per their proxy-on task types.
- **Anti-Captcha proxy addresses** (unchanged from deferred item 2):
  Anti-Captcha accepts proxy IP addresses only — hostname→IP resolution
  is a network operation performed by the engine (async-safe,
  executor-backed) before the adapter sees the proxy; adapters stay pure
  (ADR-0041).
- **Worker-context surface** (ADR-0069, now concrete): `user_agent` rides
  all token kinds across all four providers (every vendor accepts it);
  `cookies` only where the vendor API documents them — 2Captcha v2/v3/
  hCaptcha, Anti-Captcha proxy-on v2/hCaptcha, CapMonster v2/hCaptcha/
  FunCaptcha. Capsolver cookies pass through unchecked.
- **CapMonster Turnstile `cloudflare_task_type`** is a provider extra, not
  a kind (ADR-0074); v1 supports the default **`token`** mode only —
  `cf_clearance`/`wait_room` require a proxy, impossible on proxyless
  CapMonster challenges (ADR-0012), so the adapter rejects them
  pre-flight (UnsupportedChallengeError).

## Rationale

- Pinning the lists before implementation removes the largest remaining
  adapter-design unknown; each `build_payload` becomes a mechanical
  mapping against the tables.
- Sources are the vendors' own SDKs (verbatim field names) plus the live
  API docs — the same fidelity standard as the rest of the design.
- The support matrix matches provider reality rather than assuming
  uniform coverage; thin coverage is explicitly allowed (ADR-0070).

## Alternatives considered

- **Keep the lists at implementation time**: rejected; the user wants the
  surface settled before writing adapters, to avoid rework and enable the
  concrete classes to be specified up front.
- **Uniform 9-kind × 4-provider grid**: rejected; Capsolver has no GeeTest
  v4 and CapMonster/Capsolver have no text task — faking coverage would
  violate provider fidelity (goal 2).