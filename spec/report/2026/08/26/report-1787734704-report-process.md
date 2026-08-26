## Report on task: Report-process improvement

### Spec/ADR amendments

- [open] Consider recording the commit hash on each report item (or in
  `open.md`) so a suggestion can be traced to the commit that addressed
  it — currently requires git archaeology to map suggestion -> commit.

### Future-task notes

- [acted] The `State:` line question (whether it should carry a
  report-level lifecycle) — owner decided to drop the `State:` line
  entirely; status is tracked per clause only (commit `dfd9106`).

### Tooling/process

- [acted] Report schema encoded in work.md: three categories
  (Spec/ADR amendments, Future-task notes, Tooling/process), per-item
  markers (`[open]`/`[acted]`/`[needs-decision]`), header rule covering
  both indexed and ad-hoc tasks, and the `report-<epoch>-<...>` filename.
- [acted] `spec/report/open.md` created as the cross-report roll-up
  handoff; work.md instructs refreshing it each session.
- [acted] Durable learnings promoted out of ephemeral reports:
  testing.md (pytest-asyncio strict mode, `tests/` baseline, checker
  scope incl. `var/`) and bootstrap.md (slots `super()` rule, ruff `*.md`
  exclusion — the `var/` bullet intentionally dropped).
- [acted] Existing reports retrofitted into the schema and renamed to
  `report-<epoch>-task-<N>.md` (task 5-6 folded as one file).