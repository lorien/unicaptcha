# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Auto mode (ADR-0077): `unicaptcha.detect` with `detect(html, pageurl)`
  finds the captchas a page uses from its HTML source (reCAPTCHA v2/v3,
  hCaptcha, Turnstile, FunCaptcha, GeeTest v3/v4), and
  `Solver.auto_solve` / `AsyncSolver.auto_solve` solve the first match
  and return an `AutoSolveResult` with a `fill` map of DOM selectors to
  the solved values. `NoCaptchaDetectedError` (new `ErrorKind.
  NO_CAPTCHA_DETECTED`) is raised when nothing is detected. Provider
  solution reprs no longer leak full tokens (ADR-0034).
- The `geetest_v3` and `funcaptcha` examples are documented as
  illustrative: the GeeTest v3 demo `challenge` is single-use and
  Arkose's public demo blob is not worker-solvable, so those solves are
  expected to end in `NoSolutionError`.

### Changed

- 2Captcha/RuCaptcha solves now embed the project's registered `soft_id`
  (5859) by default (ADR-0072): the provider pays the project a small
  commission per solve. Pass `referral=False` to disable it, or
  `referral="<your-id>"` to credit your own software registration. Other
  providers have no registered id yet.

## [0.1.0] - 2026-09-04

### Changed

- Extracted a shared `AntiCaptchaCompatAdapterBase` in the public adapter SDK
  (`unicaptcha.adapter`, re-exported from the root) for the
  Anti-Captcha-compatible `createTask`/`getTaskResult` JSON protocol
  family: the four shipped adapters now
  inherit the response-parsing pipeline (`parse_submit_response`,
  `parse_task_status`, `parse_balance`, `map_provider_error`,
  `build_payload`) and the shared field helpers (`_decode`, `_decimal`,
  `_proxy_fields`, `_cookies`, `_soft_id`, `_single_token`, `_task_id`,
  ...). `unicaptcha.errors.error_from_kind` is now public so third-party
  adapters can raise mapped provider errors without importing `_internal`
  (ADR-0041). No behavior change. The Anti-Captcha proxy-hostname error
  message no longer names the challenge class.

### Fixed

- Example scripts are now import-safe: executable code lives under
  `if __name__ == "__main__":` guards, and `tests/test_examples.py`
  executes each example against a respx-mocked 2Captcha transport (no
  credits) — catching the class of facade-attribute misuse that
  `compile()`-only checks missed (e.g. the former `examples/sync/proxy.py`
  generic `solve()` call).
- Text captcha kind default solve budget: `total_timeout` raised to
  120 s (was 30 s, shared with image). Two live 2Captcha text solves
  exceeded the old budget; image keeps 30 s.
- 2Captcha reCAPTCHA v3 solution classification: the live v3 solution
  shape is `gRecaptchaResponse` + `token` **without** a `score` field;
  it was previously mis-classified as a reCAPTCHA v2 solution. `score`
  is `None` when the provider omits it.
- CapMonster GeeTest v4 wire payload: the captcha id now rides `gt`
  (CapMonster's SDK requires it unconditionally, v4 included) and
  `risk_type` alone rides `initParameters.riskType`; previously the id
  was mis-placed inside `initParameters` and `gt` was omitted.

### Added

- Universal multi-provider clients: `Solver` (blocking) and `AsyncSolver`
  (asyncio-native), with an adapter registry, kind dispatch, and provider
  selection (pin a provider or pick uniformly among supporting adapters).
- Per-provider facades (`TwoCaptchaClient`, `AntiCaptchaClient`,
  `CapMonsterClient`, `CapsolverClient`, and their async counterparts) with
  one convenience method per kind and full constructor and per-call
  parameter parity.
- Four provider adapters speaking the modern JSON
  `createTask`/`getTaskResult` protocol: 2Captcha, Anti-Captcha, CapMonster
  Cloud (proxyless), and Capsolver.
- Nine captcha kinds with symmetric challenge/solution class trees: image,
  text, reCAPTCHA v2, reCAPTCHA v3, hCaptcha, FunCaptcha, GeeTest v3,
  GeeTest v4, and Cloudflare Turnstile — including enterprise flags,
  proxy/worker-context fields, and strict field validation.
- A unified exception hierarchy rooted at `UnicaptchaError` with an
  `ErrorKind` enum and the verbatim provider response preserved on
  `raw_response`.
- Strictly-typed configuration objects: `NetworkConfig`, `TimeConfig`,
  `RetryConfig`, `Proxy`/`ProxyKind`, and `SecretStr` for API keys.
- A two-phase submit/await workflow: `submit()` returns a `TaskTicket`,
  `wait()` collects it, and `wait_ref()` polls a persisted `TaskRef`; the
  submit-ready fast path returns instant tasks without polling.
- Auxiliary operations: `get_balance`, `get_task_status`,
  `report_bad_result`, `report_good_result`, and `get_abandoned_tasks`.
- A public adapter SDK (`BaseAdapter`, `Endpoints`) for authoring third-party
  providers, with a reference implementation included in the test suite.
- Task lifecycle events (`on_event=`) and flat logging that never includes
  API keys or solution tokens.
- An abandoned-task registry that survives client close, with advisory
  per-client recovery.
- Strict typing and tooling: Python 3.11+, fully annotated, mypy and pyright
  strict, ruff, and slotscheck.
- Base-URL mirror support (e.g. RuCaptcha via `base_url=`) and referral
  embedding for the built-in adapters.
- An `examples/` directory: runnable per-use-case scripts in `sync/` and
  `async/` flavors covering every captcha kind, two-phase batch, aux ops,
  events, errors, and proxy usage, demonstrated on 2Captcha with public
  demo sitekeys.
