# Competitor analysis: Go and Python

GitHub survey (2026-08-24, GitHub search API) of universal
multi-provider CAPTCHA-solving client libraries — the niche unicaptcha
targets. Complements the unicaps/anycaptcha analyses recorded in ADRs
0019, 0034, 0040, 0067-0072.

## Python (contested market)

The only ecosystem with real universal libraries.

- **sergey-scat/unicaps** (234★) — the reference incumbent; analyzed
  throughout our ADRs. Sync + async clients, 10 kinds, 6 services
  (2Captcha, RuCaptcha, Anti-Captcha, azcaptcha, cap.guru, DBC).
  `CaptchaSolver(CaptchaSolvingService.TWOCAPTCHA, api_key=...)`,
  per-kind convenience methods, `solved.report_good()`, cost metadata.
  Effectively dormant: last push 2025-05 (>1 year). Source of the
  known-bug pattern our ADR-0019/0034 test commitments target
  (annotations that lie; truthiness cost check turning 0 into None;
  dead payload fields).
- **alenkimov/anycaptcha** (46★) — spiritual successor ("special
  thanks to unicaps"). Async-only, 9 services (adds Capsolver,
  multibot), 10 kinds, report_good/report_bad, Path image input,
  proxy support via better-proxy. Active. Error mapping via if/elif
  chains (its own TODO admits this); no sync tier.
- **Matthew17-21/Captcha-Tools** (78★ pip `captchatools`) — 4
  providers (Capmonster/2Captcha/Anticaptcha/Capsolver) behind a
  stringly-typed lowest-common-denominator API:
  `new_harvester(solving_site=..., captcha_type="v2") -> get_token()`
  returns a bare string. No typing, no provider fidelity.
- Single-provider crowd (not universal): official `2captcha-python`
  (793★), `ad-m/python-anticaptcha` (230★),
  `AndreiDrang/python3-anticaptcha` (163★), official CapMonster /
  Capsolver / Anti-Captcha SDKs. NopeCHA / Botright (~1k★) are
  AI/self-hosted solvers — different category.

## Go (one decent typed attempt)

- **justhyped/gocaptcha** (51★) — strongest Go design: 2Captcha +
  AntiCaptcha (+ CapMonster via custom-domain override), 5 kinds
  (reCAPTCHA v2/v3, image, hCaptcha, Turnstile), single
  `Solve(captcha, provider)` surface, extensible `IProvider`
  interface (adapter-SDK idea), MIT. No kind/solution taxonomy, no
  status-query semantics.
- **Matthew17-21/Captcha-Tools** (Go port, 78★) — same stringly-typed
  design as the Python tool; bare token-string returns.
- **median/captchago** (5★) — 5 services (incl. AnyCaptcha), 5 kinds;
  referral-link-heavy, minimal traction.
- Single-provider: official `2captcha-go` (145★), `capsolver-go`
  (27★), `anti-captcha/anticaptcha-go` (3★), `nuveo/anticaptcha`
  (51★, stale). `Hyper-Solutions/hyper-sdk-go` (63★) is sensor
  generation, not a solving-service client.

## Takeaway

Python is the only contested market: unicaps (big, stale, untyped)
and anycaptcha (active, async-only) leave exactly the gap unicaptcha
fills — strict typing, provider fidelity via per-provider classes,
honest error/status semantics, two-phase submit/wait, public adapter
SDK. Go has one small typed attempt; nothing approaches the design
depth. (Ruby/JS/TS/Rust survey, 2026-08-24: the niche is empty or
toy-grade in all four.)
