# Task 13: CapMonster adapter + facade

Status: new

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