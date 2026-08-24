# ADR-0074: Cloudflare Turnstile as ninth captcha kind

**Status:** Accepted (amends ADR-0002, ADR-0070)
**Date:** 2026-08-24

## Context

Competitor-analysis survey (2026-08-24; `spec/ref/competitors.md` and the
per-project reports behind it) re-examined the kind taxonomy against what
providers and rival libraries actually ship. Cloudflare Turnstile was
excluded from v1 by ADR-0002's scope freeze — but it was never added to
deferred.md, so ADR-0002's "deferred by name in deferred.md" claim has
been dangling since ADR-0070 rewrote that sentence's neighborhood.

The survey's findings on Turnstile:

- **All four v1 providers support it**: 2Captcha `method=turnstile`;
  Anti-Captcha `TurnstileTaskProxyless` / `TurnstileTask`; CapMonster
  `TurnstileTask` (with `token`, `cf_clearance`, and `wait_room` modes);
  Capsolver `AntiCloudflareTask`. It is the only candidate kind with
  unanimous provider coverage.
- **Every surveyed competitor ships it**: gocaptcha and capbuster (Rust),
  captchatools (Go port), nopecha (`solve_cloudflare_turnstile`), the
  official 2Captcha SDK (`turnstile` among its 37 methods).
- **Zero structural novelty**: two required universal fields and a
  single-token solution — the hCaptcha shape exactly. ADR-0070's own
  inclusion test (high demand, wide multi-provider support, no structural
  novelty) is satisfied; its exclusion was a scope-freeze artifact, not
  a recorded decision.

## Decision

- `TurnstileChallenge` kind base: **keyword-only** fields (ADR-0066) —
  `sitekey: str` and `pageurl: str` required; `action: str | None`,
  `c_data: str | None`, `chl_page_data: str | None` optional (optional
  string flags follow the hCaptcha `rqdata` precedent from ADR-0070).
  `proxy` / `user_agent` / `cookies` placement per ADR-0012 / ADR-0069.
- `TurnstileSolution` abstract base: `token: str` (non-instantiable rule,
  ADR-0035/0056).
- **Provider extras ride deferred item 2** like every kind's: CapMonster's
  `cloudflare_task_type` modes (`token` default / `cf_clearance` /
  `wait_room`, the latter two proxy-requiring), `html_page_base64`,
  `api_js_url`; Capsolver's proxy-required flavor.
- Kind count 8 → 9; ~8 new concrete classes across the four providers.
- ADR-0002's dangling deferred-reference claim is resolved herewith;
  deferred.md item 13 never listed Turnstile and keeps its actual deferrals
  (KeyCaptcha, Capy Puzzle, TikTok) unchanged.

## Rationale

- The one kind where provider coverage is total and competitor consensus
  is universal; omitting it from a "universal" library's README table is
  the most exploitable gap in our v1 surface.
- Cheapest structural addition possible in the taxonomy — mechanical
  after ADR-0064 (dispatch), ADR-0066 (call style), and ADR-0070 (flags
  pattern) settled the surrounding design.
- `cf_clearance`/`wait_room` stay provider extras, not kinds: payload
  variation within one provider task type, per ADR-0070's
  flags-not-kinds rule for Enterprise reCAPTCHA.

## Alternatives considered

- **Stay at 8 kinds, fix only the dangling claim**: rejected; leaves the
  only unanimously-supported kind out of v1 for no recorded reason.
- **Separate `*CfClearance*` kinds**: rejected; doubles the class grid
  for payload variation (ADR-0070 precedent).
- **Defer Turnstile properly by name**: superseded by this ADR; nothing
  about the deferral rationale (single-provider or structural novelty)
  applies to it.
