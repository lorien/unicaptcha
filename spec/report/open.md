# Open report items

Roll-up of every `[open]` / `[needs-decision]` item across `spec/report/`.
Refreshed at the end of each task session (see `spec/skills/work.md`).
Links point at the source reports under `spec/report/2026/08/26/`.

## Spec/ADR amendments

- [report-process] Consider recording the commit hash on report items (or
  in open.md) so a suggestion is traceable to the commit that addressed
  it. — [report](2026/08/26/report-1787734704-report-process.md)
- [task 1] ADR-0019: record the ruff `*.md` format exclusion and that both
  type checkers are package-scoped. —
  [report](2026/08/26/report-1787697485-task-1.md)
- [task 1] testing.md: make checker package-scope explicit in the
  documented commands. —
  [report](2026/08/26/report-1787697485-task-1.md)
- [task 2] ADR-0067: re-scope TaskTicket non-constructibility to
  doc-only. — [report](2026/08/26/report-1787700294-task-2.md)
- [task 2] ADR-0014: pin strict `SecretStr` equality (TypeError on
  non-SecretStr, None -> False, hash-probe consequence). —
  [report](2026/08/26/report-1787700294-task-2.md)
- [task 2] architecture.md: `Proxy` sketch field order vs dataclass
  ordering. — [report](2026/08/26/report-1787700294-task-2.md)
- [task 2] architecture.md: `_internal/` listing could mention config
  resolution (`_internal/config.py`). —
  [report](2026/08/26/report-1787700294-task-2.md)
- [task 3] Share the 1:1 `ErrorKind`-to-class table in one module so
  adapter tests (task 17) reuse it. —
  [report](2026/08/26/report-1787701942-task-3.md)
- [task 4] architecture.md: record `TaskEvent` field-default decision. —
  [report](2026/08/26/report-1787702841-task-4.md)
- [task 5-6] Note in the spec/plan that tasks 5+6 are one unit. —
  [report](2026/08/26/report-1787703686-task-5-6.md)

## Future-task notes

- [task 1] CI 3.14t informational job depends on setup-uv `t`-suffix
  support; `continue-on-error` keeps it non-blocking. —
  [report](2026/08/26/report-1787697485-task-1.md)
- [task 2] Confirm `slots=True` + frozen pickling on the 3.11 floor via CI.
  — [report](2026/08/26/report-1787700294-task-2.md)
- [task 3] Behavioral error requirements (chaining, wrong-provider
  `TypeError`, malformed-response `ProviderError` with `__cause__`) must
  be tested in tasks 7-10. —
  [report](2026/08/26/report-1787701942-task-3.md)
- [task 4] Engine (task 9) and adapters (tasks 11-14) should share/import
  the `error_kind` matrix. —
  [report](2026/08/26/report-1787702841-task-4.md)
- [task 4] Clients (tasks 9/10) must consume `_internal/handlers.py`
  (`check_sync_handler` on the sync tier; flat logger for the discard
  WARNING). — [report](2026/08/26/report-1787702841-task-4.md)
- [task 5-6] Adapter tasks (11-14): confirm GeeTest v4 `gen_time` is a
  `str` on every provider. —
  [report](2026/08/26/report-1787703686-task-5-6.md)
- [task 5-6] Provider extras and `proxy`/`user_agent`/`cookies` land on
  provider subclasses in tasks 11-14. —
  [report](2026/08/26/report-1787703686-task-5-6.md)

## Tooling/process

- [task 4] Consider a shared `_internal/log.py` for the flat `unicaptcha`
  logger if logging call sites proliferate. —
  [report](2026/08/26/report-1787702841-task-4.md)