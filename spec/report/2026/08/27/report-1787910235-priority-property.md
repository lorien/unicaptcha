## Report on task: priority property for plan.md tasks

### Done

- Added a numeric `Priority:` line to the task model in `spec/docs/plan.md`:
  it sits right after the `Status:` line; default `0` for new records;
  higher value = more important; `Priority: -1` = deferred (never
  auto-picked until the priority is raised).
- Selection rule changed from file order to priority: pick the
  highest-priority `new` task, ties break by file order, `-1` tasks are
  skipped. The owner now reprioritizes by editing `Priority:` values
  instead of physically reordering records.
- Assigned `Priority: -1` to all 19 current records (the existing
  priority-less backlog is parked, per owner; new records default to `0`).
- Updated `spec/skills/task_tracking.md`: record structure includes the
  `Priority:` line, adding starts at `Priority: 0`, choosing picks the
  highest-priority `new` record (ties by file order, `-1` skipped),
  deferring = set `Priority: -1`, and the archived record drops the
  `Priority:` line.
- Updated `spec/skills/work.md`: task selection wording changed from
  "topmost `new` task" to "highest-priority `new` task; deferred tasks
  with `Priority: -1` are not picked".
- Updated `spec/skills/report_tracking.md`: noted that the archived
  record drops the plan-time `Priority:` line.
- Verification: `uv run pytest` (452 passed), `uv run ruff check .`,
  `uv run ruff format --check .`, `uv run mypy unicaptcha`,
  `uv run pyright unicaptcha`, `uv run slotscheck unicaptcha` — all clean.
  Counts confirm 19 records / 19 `Status: new` / 19 `Priority: -1`.

### Spec/ADR amendments

- None; the priority model is a plan/task-tracking workflow change, not an
  ADR decision.

### Future-task notes

- All 19 plan.md tasks are currently deferred (`Priority: -1`); the owner
  will assign real priorities when ready to pick work again.
- When the observations-backlog review eventually runs, it can also prune
  or re-prioritize the migrated records.

### Tooling/process

- [acted] Priority replaces file-order as the selection mechanism; file
  order is now only a tie-breaker. New records default to `0`, so a task
  is only "deferred" by explicit `Priority: -1` — matching the owner's
  "to defer means assign -1" rule.