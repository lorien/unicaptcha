# Task 13: CapMonster adapter + facade

Status: done

First read `var/analysis-py-capmonster-python.md`.

Implement `provider/capmonster/`:

- `challenge.py`: concrete challenge subclasses per ADR-0076 — proxyless
  (no proxy field), image module/threshold extras, Turnstile
  `cloudflare_task_type` restricted to `token` in v1.
- `solution.py`: concrete solution subclasses.
- `adapter.py`: `CapMonsterAdapter` — payload build + parse, error
  mapping; report coverage (CapMonster lacks report-bad; `*_supported`
  returns False).
- `client.py`: `CapMonsterClient` / `AsyncCapMonsterClient` facades.

References: ADR-0001, ADR-0007, ADR-0012, ADR-0051, ADR-0061, ADR-0074,
ADR-0076, ADR-0068.

Done:

- `challenge.py`: eight concrete frozen-slots challenges (no text kind —
  CapMonster has none). `CapMonsterImageChallenge` validates `module_name`
  against the SDK's 17 `TextModules`, `threshold` 0-100, `numeric` ∈
  {0,1}; v3 `min_score` validated 0.1-0.9; Turnstile `cloudflare_task_type`
  restricted to `"token"` (cf_clearance/wait_room need a proxy, impossible
  under the proxyless rule). Proxyless everywhere (ADR-0012); v2 adds an
  `action` extra (→pageAction); hCaptcha adds `fallback_to_actual_ua`.
- `solution.py`: eight concrete solutions, no extras (CapMonster returns
  raw solution dicts; SDK captures no worker context).
- `adapter.py`: `CapMonsterAdapter` ("capmonster",
  https://api.capmonster.cloud) — envelope + trinary `softId`; single
  task-type names per SDK (`RecaptchaV2Task`, `RecaptchaV2EnterpriseTask`,
  `RecaptchaV3TaskProxyless`/`RecaptchaV3EnterpriseTask` as separate types,
  `HCaptchaTask`, `FunCaptchaTask`, `GeeTestTask` v3/v4, `TurnstileTask`,
  `ImageToTextTask`); v2 enterprise funnels `data_s`→`enterprisePayload
  {'s':…}`; GeeTest v4 builds `initParameters` from captcha_id+risk_type
  with **no `gt`** (per pinned spec); no proxy serialization anywhere;
  lenient parsing (ADR-0040); error-code table; 4-state parse; balance;
  reports default-off (CapMonster has no report API — both
  `*_supported` → False).
- `client.py`: `CapMonsterClient` / `AsyncCapMonsterClient` facades — full
  constructor parity minus `adapters` (`proxy=` kept inert for parity),
  **eight** `solve_*` methods (no `solve_text`), time/retry/on_event
  parity, two-phase, aux ops accepting `TaskRef | int`.
- Package re-exports in `provider/capmonster/__init__.py`.
- Tests: `tests/test_capmonster.py` (17 tests) — challenge validations
  (module enum, threshold, numeric 0/1, v3 range, turnstile token-only),
  payloads per kind (incl. enterprise {'s':…}, v4 initParameters without
  gt, hCaptcha data/fallbackToActualUA, turnstile data/pageData), parse
  states, error mapping, reports-default-off, sync + async facades.
- Discrepancies tracked in the session report (GeeTest v4 `gt` and worker
  context vs SDK, v2 enterprise payload source, turnstile token-mode
  strictness, image numeric 0/1, docs 403-blocked).