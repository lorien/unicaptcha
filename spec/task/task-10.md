# Task 10: Solver / AsyncSolver universal client

Status: new

Implement `unicaptcha/client.py`:

- `Solver` / `AsyncSolver`: constructor `adapters` positional +
  keyword-only (`name`, `user_agent`, `proxy`,
  `abandoned_registry_limit`, `time`, `retry`, `network`,
  `network_client`, `on_event`).
- Adapter registry keyed by `provider`; duplicate providers rejected
  (`ValueError`); non-adapter objects rejected (`TypeError`).
- Dispatch: concrete challenge class → its adapter; kind base + `provider=`
  → that adapter; kind base + `provider=None` → uniform random choice
  among supporting adapters, upcast before build_payload.
- Operations: `solve`, `submit`, `wait`, `wait_ref`, `get_task_status`,
  `get_balance`, `report_bad_result`, `report_good_result`,
  `get_abandoned_tasks`; status queries answer, operations raise.
- Use-after-close raises `ClientClosedError`; context managers.
- Sync + async tiers as peers (no wrapper magic); shared engine.

References: ADR-0003, ADR-0005, ADR-0033, ADR-0036, ADR-0037, ADR-0045,
ADR-0050, ADR-0051, ADR-0055, ADR-0062, ADR-0064, ADR-0067.