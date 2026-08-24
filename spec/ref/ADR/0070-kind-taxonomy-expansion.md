# ADR-0070: Kind taxonomy expansion — FunCaptcha, GeeTest v3/v4, enterprise flags

**Status:** Accepted (amends ADR-0002; extends ADR-0030's timing table; amended by ADR-0074: Turnstile added as ninth kind)
**Date:** 2026-08-23

## Context

Competitive analysis (unicaps/anycaptcha, session 2026-08-23) showed
both libraries covering 10-11 kinds against our five. Demand ranking
and structural risk split the field cleanly (owner decision): the
multi-provider, high-demand kinds enter scope; the single-provider or
structurally novel ones are deferred by name.

## Decision

### New kinds in v1 scope (ADR-0002 amended: five -> eight)

| Kind base | Universal challenge fields | Solution base | Solution fields |
|---|---|---|---|
| `FunCaptchaChallenge` | `public_key`, `pageurl` | `FunCaptchaSolution` | `token: str` |
| `GeeTestChallenge` (v3) | `gt_key`, `challenge`, `pageurl` | `GeeTestSolution` | `challenge`, `validate`, `seccode` |
| `GeeTestV4Challenge` | `captcha_id`, `pageurl` | `GeeTestV4Solution` | `captcha_id`, `lot_number`, `pass_token`, `gen_time`, `captcha_output` |

- Provider extras (e.g. FunCaptcha's `blob`, `service_url`) ride the
  deferred-#2 field-list work like every existing kind's extras.
- All new challenge fields are keyword-only, keyword-required
  (ADR-0066: multi-field kinds, no single payload field).
- Multi-field solutions need no structural change
  (`RecaptchaV3Solution` precedent).
- Provider coverage is defined by adapters listing the challenge
  classes; kind-level solve's random selection skips non-supporting
  adapters (ADR-0064 handles this already). Thin coverage is fine.

### Enterprise as flags, not kinds

Existing kinds gain keyword-only fields (flag precedent:
`invisible`):

- `RecaptchaV2Challenge`, `RecaptchaV3Challenge`:
  `is_enterprise: bool = False`, `data_s: Mapping[str, str] | None`,
  `api_domain: str | None`
- `HCaptchaChallenge`: `is_invisible: bool = False`,
  `rqdata: str | None`

Separate `*Enterprise*` kinds rejected: doubles the V2/V3 class grid
for what is payload variation.

### Timing table extension

ADR-0030's engine table gains rows for FunCaptcha and GeeTest v3/v4 —
GeeTest-class and FunCaptcha cadence near reCAPTCHA-class (poll ~5 s,
total ~120 s); exact values set at implementation against provider
guidance.

### Deferred kinds (recorded by name in deferred.md)

- **KeyCaptcha** — 2Captcha-family only, low demand
- **Capy Puzzle** — single provider
- **TikTok** — structural novelty (cookies-typed solution, no payload
  field, secrets-adjacent repr questions) and single-provider

Third-party adapters may cover them meanwhile (SDK, ADR-0041/0048/
0064).

## Rationale

- Chosen kinds: high demand + wide multi-provider support + zero
  structural novelty — mechanical to add after ADR-0064 (dispatch)
  and ADR-0069 (worker context) settled the surrounding design.
- Flags over kinds keeps the class grid linear; `invisible` already
  proved the pattern.

## Alternatives considered

- **All-in (incl. TikTok/KeyCaptcha/Capy)**: rejected; TikTok's
  cookies-solution is real design work, single-provider kinds are
  dead weight in v1.
- **Full deferral (stay five kinds)**: rejected; FunCaptcha/GeeTest
  are the top-demand gaps competitors exploit.
- **Separate Enterprise kinds**: rejected; class-grid doubling for
  payload variation.
