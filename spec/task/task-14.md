# Task 14: Capsolver adapter + facade

Status: done

First read `var/analysis-py-capsolver-python.md`.

Implement `provider/capsolver/`:

- `challenge.py`: concrete challenge subclasses per ADR-0076 (GeeTest
  v3 only; Turnstile via `AntiCloudflareTask` with `metadata`; dict-style
  pass-through extras).
- `solution.py`: concrete solution subclasses.
- `adapter.py`: `CapsolverAdapter` — payload build + parse, instant-task
  fast path (`instant_answer`), referral embedding (ADR-0072), error
  mapping incl. HTTP-status keyed kinds.
- `client.py`: `CapsolverClient` / `AsyncCapsolverClient` facades.

References: ADR-0001, ADR-0007, ADR-0051, ADR-0061, ADR-0071, ADR-0072,
ADR-0075, ADR-0076.

Done:

- **Core type change**: public `task_id` widened `int` → `int | str`
  (TaskRef/TaskResult/TaskStatusResult/SubmitAccepted/TaskEvent +
  engine `_event` + `BaseAdapter.build_task_status`) — Capsolver addresses
  tasks by UUID string (verified docs). Capsolver facades' aux ops accept
  `TaskRef | int | str`.
- `challenge.py`: eight concrete frozen-slots challenges (no text).
  `CapsolverRecaptchaV3Challenge` rejects `is_enterprise` (no v3-enterprise
  type); `CapsolverTurnstileChallenge` rejects `chl_page_data` (only
  action/cdata in metadata); v2 adds `action` (→pageAction, the `sa`
  payload); image adds `module`; GeeTest v4 included with `captcha_id`/
  `risk_type`.
- `solution.py`: eight concrete solutions, no extras.
- `adapter.py`: `CapsolverAdapter` ("capsolver",
  https://api.capsolver.com) — 5-field proxy block (hostnames OK),
  `_task_id` returns `int | str` (numeric strings normalize to int),
  instant fast path (recognition ImageToText answers inline, ADR-0075),
  `status: "failed"` → NO_SOLUTION, error-code table, solution dispatch
  with `solution.type` disambiguation (turnstile/funcaptcha/hcaptcha),
  balance. Referral accepted but inert (no affiliate-id field on
  Capsolver); no `softId` in payloads.
- `client.py`: `CapsolverClient` / `AsyncCapsolverClient` facades — full
  constructor parity minus `adapters`, eight `solve_*` methods (no text),
  time/retry/on_event parity, two-phase, aux ops accepting
  `TaskRef | int | str`.
- Package re-exports in `provider/capsolver/__init__.py`.
- Tests: `tests/test_capsolver.py` (17 tests) — string/int taskId,
  instant fast path, failed→NO_SOLUTION, payloads per kind (proxy types,
  enterprise {'s':…}, captchaId/riskType, AntiTurnstileTaskProxyLess
  metadata, v3-no-enterprise, turnstile-no-chl_page_data), solution
  dispatch, sync + async facades.
- Discrepancies tracked in the session report (taskId type widening,
  GeeTest v4 coverage now supported by docs, Turnstile task type name,
  hCaptcha/FunCaptcha docs pages absent, v3 enterprise unsupported,
  referral inert, image proxyless).