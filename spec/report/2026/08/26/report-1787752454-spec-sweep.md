## Report on task: Spec/ADR consistency sweep

### Spec/ADR amendments

- [acted] Amended ADR-0019 (ruff `*.md` format exclusion; both type
  checkers package-scoped), ADR-0067 (TaskTicket doc-only enforcement),
  ADR-0014 (strict `SecretStr` equality + hash-probe consequence),
  ADR-0053 (`referral` keyword-only signature), ADR-0036 (singular-file
  exception for `adapter.py`), ADR-0041 (public modules may consume
  `_internal` helpers).
- [acted] Pinned in architecture.md: `Proxy` field-order note, `TaskEvent`
  field defaults, `_internal/` config-resolution member,
  `map_provider_error -> tuple[ErrorKind, str]`.
- [acted] testing.md: `uv run pyright unicaptcha` (scope in the command,
  mirroring `mypy unicaptcha`).
- [acted] task-5.md / task-6.md: note the tasks 5+6 unit.
- [open] Commit-hash traceability on `[acted]` markers (report-process
  item) remains undecided; this sweep annotated markers with descriptive
  notes ("spec sweep 2026-08-26") rather than hashes — adopting the item
  would append hashes going forward.

### Future-task notes

- [open] Left task-scoped (not part of this sweep): registration
  `TypeError` check (9/10), `default_task_config` consumption (9),
  `error_kind` matrix sharing (9), clients consuming `_internal/handlers`
  (9/10), shipped-adapter `__slots__` (11-14), GeeTest v4 `gen_time`
  confirm (11-14), provider extras/proxy placement (11-14), reference
  adapter `_internal` check (15), shared ErrorKind table (17), 3.11
  pickle + 3.14t CI confirmation (unverified until CI runs).

### Tooling/process

- [acted] All 12 source-report items + the report-rollup derived-query
  principle flipped to `[acted]` with sweep notes (13 marker flips).
- [acted] Followed the (B) option-1 approach (dedicated sweep) over
  folding into tasks; skipped the optional deferred.md #22 record (owner
  decision — a completed chore, not a deferred decision).