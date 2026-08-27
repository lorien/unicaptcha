## Report on task: workflow redesign — plan.md, no task numbers, interactive-only

### Done

- `spec/docs/plan.md`: task headers dropped to names (`## Adapter
  golden-payload tests`, `## README + CHANGELOG`); only `new` status;
  priority expressed by file order (topmost `new` picked first, owner
  reorders); ad-hoc tasks noted as untracked.
- `spec/skills/task_tracking.md`: no task numbers; only `new`; choose the
  topmost `new` record; append new records at the end; "When Work Is
  Blocked" replaces the failure section (no failure files, status
  unchanged); ad-hoc boundary note.
- `spec/skills/report_tracking.md`: uniform `report-<epoch>-<slug>.md`
  naming with `## Report on task: <title>`; reports written only when work
  is complete and committed; plan tasks archive the record (`### Task
  (archived from plan.md)` + `### Done` + suggestion categories), ad-hoc
  opens with `### Done` + categories.
- `spec/skills/work.md`: ad-hoc path (work not in plan.md); approval gate
  kept; report + record-removal only for plan tasks; no commit/report
  unless a task was worked to completion; "When work is blocked" (present
  to user, no failure files).

### Spec/ADR amendments

- [acted] Dropped the task-`failed` status and `var/task.failed`
  mechanism entirely; blockers are handled live in interactive sessions.
- [acted] Dropped task numbers: no high-water-mark bookkeeping, no report
  `task-<N>` naming; references use task titles and report slugs.
- [open] `spec/skills/task.md` still says "create corresponding task
  records in `spec/docs/plan.md`" — accurate under the new model; no
  change needed unless feature-planning semantics shift.

### Future-task notes

- None (tasks 17/18 bodies unchanged in plan.md, now titled).

### Tooling/process

- [open] Reports are the only archive of done tasks; the still-open
  suggestion set is derived via
  `grep -rn "\[open\]|\[needs-decision\]" spec/report/`. With slug
  (not numeric) report names, linking a report to a task relies on the
  title in the first line — keep titles stable when archiving.