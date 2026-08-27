# Task 12: Anti-Captcha adapter + facade

Status: done

First read `var/analysis-py-anticaptcha-python.md`.

Implement `provider/anticaptcha/`:

- `challenge.py`: concrete challenge subclasses per ADR-0076 (nine kinds;
  text via API `TextCaptchaTask`; enterprise flags; min_score
  validation 0.5/0.7/0.9).
- `solution.py`: concrete solution subclasses (incl. `user_agent` /
  `resp_key` extras).
- `adapter.py`: `AntiCaptchaAdapter` — payload build + parse, error
  mapping, report pairs; proxy addresses IP-only (engine resolves
  hostname→IP async-safe, executor-backed; adapter stays pure).
- `client.py`: `AntiCaptchaClient` / `AsyncAntiCaptchaClient` facades.

References: ADR-0001, ADR-0007, ADR-0051, ADR-0061, ADR-0076, ADR-0041,
ADR-0040.

Done:

- `challenge.py`: nine concrete frozen-slots challenges with ADR-0076
  extras (`language_pool` on image; `lang` on text per pinned spec;
  `stoken`/`data_s`/enterprise on reCAPTCHA v2; v3 `min_score` validated
  against 0.5/0.7/0.9 raising InvalidChallengeError; FunCaptcha
  `data`/`service_url`; GeeTest v3 `api_server`/`geetest_lib`, v4
  `risk_type`/`api_server`; proxy-capable fields per the §2 table).
- `solution.py`: nine concrete solutions; `AntiCaptchaRecaptchaV2Solution`
  and `AntiCaptchaHCaptchaSolution` carry optional `user_agent`/`resp_key`
  extras (SDK captures `solution["userAgent"]`/`respKey`).
- `adapter.py`: `AntiCaptchaAdapter` ("anti-captcha",
  https://api.anti-captcha.com) — envelope builder with trinary `softId`
  referral, per-kind payloads cross-verified against the official SDK
  clone (task-type strings proxyless/proxy-conditional, camelCase
  Turnstile `cData`/`chlPageData`, GeeTest v4 `gt`-rides-captcha_id +
  `version:4` + `initParameters.riskType`), **IP-literal proxy
  enforcement** (hostnames → InvalidChallengeError pre-flight; engine
  resolution deferred), lenient JSON parsing (ADR-0040), error-code table,
  4-state `parse_task_status`, balance. Report pairs default-off: per-kind
  report endpoints (reportIncorrectImageCaptcha/Recaptcha/CorrectRecaptcha/
  Hcaptcha) don't fit the TaskRef-based fixed-path engine (owner decision;
  kind-aware reporting deferred).
- `client.py`: `AntiCaptchaClient` / `AsyncAntiCaptchaClient` facades
  (peers over own TaskEngine), full constructor parity minus `adapters`,
  nine typed `solve_*` methods with time/retry/on_event parity, two-phase
  submit/wait/wait_ref, aux ops accepting `TaskRef | int`.
- Package re-exports in `provider/anticaptcha/__init__.py`.
- Tests: `tests/test_anticaptcha.py` (17 tests) — payloads per kind
  (incl. proxyless/proxy types, v3 score validation, IP-only rejection,
  softId trinary), parse states + solution extras, error mapping, sync +
  async facade round trips, wrong-provider rejection.
- Owner decisions this session: report pairs default-off; IP-literal
  enforcement now (engine resolution deferred); `lang→lang` on text kept
  per pinned spec (unverified against apidoc — JS-rendered); GeeTest v3
  solution keys to verify against live examples at golden-payload time
  (task 17).