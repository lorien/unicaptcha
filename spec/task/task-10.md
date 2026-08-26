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

## Done

- `unicaptcha/client.py`: `Solver` / `AsyncSolver` as peers (ADR-0003).
  Constructor: `adapters` positional+required; keyword-only `name`,
  `user_agent`, `proxy`, `abandoned_registry_limit`, `time`, `retry`,
  `network`, `network_client`, `on_event`.
- Registration: non-adapters -> `TypeError`; duplicate providers ->
  `ValueError("provider 'x' registered twice")` (ADR-0037); empty list ->
  `ValueError`. Eager transport + engine construction. Sync tier rejects
  coroutine-function handlers at attachment AND per call (`what=` labels
  both sites).
- `abandoned_registry_limit`: default **1000** per ADR-0038; explicit
  `None` = unbounded (owner decision Q1 — architecture sketch's `= None`
  default was an oversight vs ADR-0038; sketch should be corrected).
- `_internal/routing.py`: dispatch matrix — concrete class exact match
  (contradicting `provider=` -> `TypeError` naming both parties);
  kind-base instance with `provider=` name (unknown -> `TypeError`);
  kind-base + None -> uniform random among supporting adapters via
  injectable `uniform_choice` hook; unmatched -> `TypeError`;
  unsupported kind -> `UnsupportedChallengeError`. Kind-base instances
  upcast to the adapter's concrete class (universal fields) before
  payload building; client default proxy applied only to concrete
  challenges carrying a `proxy` field (challenge's own wins; WARNING
  when the field is missing, ADR-0012). Pre-flight failures invoke a
  callback carrying best-known provider hint -> client emits
  PRE_FLIGHT_FAILED (skip emission when no provider is resolvable),
  matching the error_kind matrix.
- Operations delegate to engines: `solve`, `submit`, `wait`, `wait_ref`,
  `get_task_status`, `get_balance` (instance/class/string discriminator),
  `report_bad/good_result`, `get_abandoned_tasks` (readable after close).
- Lifecycle: idempotent close/aclose, context managers (`with`/`async
  with`), use-after-close -> `ClientClosedError`.
- Root re-exports `Solver`, `AsyncSolver`.
- Tests: 225 total passing — registration errors, dispatch matrix,
  random-pick pinning (monkeypatched uniform_choice), upcast fidelity
  (universal fields land on the concrete class), proxy warning path,
  pre-flight emissions incl. skip-without-hint, two-phase and aux ops
  both tiers, context managers, use-after-close.
- Full suite green (ruff, mypy strict, pyright strict, slotscheck).
  No hard-coded credentials.