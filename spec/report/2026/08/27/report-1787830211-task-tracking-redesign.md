## Report on task: task-tracking redesign (plan.md + archive-to-report)

### Spec/ADR amendments

- [acted] Created `spec/docs/plan.md` as the single home of open tasks:
  records with `## Task {N}: {title}`, `Status:` (`new`/`failed`),
  body, optional `References:`. Done tasks are removed from plan.md and
  archived into the session's report; failed tasks stay in plan.md with a
  `Reason:` line. Added to the `spec/docs/index.md` documents table.
- [acted] Rewrote `spec/skills/task_tracking.md` (plan.md model: add/
  choose/finish/fail rules, failed > new priority, ordering by number) and
  `spec/skills/report_tracking.md` (archive-on-done: `### Task (archived
  from plan.md)` + `### Done` + the three suggestion categories with
  `[open]`/`[acted]`/`[needs-decision]` markers).
- [acted] Updated `spec/skills/work.md` (select from plan.md, archive +
  remove on finish, failed recorded in the task record) and
  `spec/skills/task.md` (create records in plan.md).
- [acted] Removed `spec/task/` (index + task-1..18 files); the 16 done
  tasks were already summarized in their `spec/report/` files, so no
  archival migration was needed (owner-approved start-clean).
- [acted] Dropped the `var/task.failed` mechanism; failure reasons now
  live in the task record. `var/plan.completed` (no more open tasks)
  unchanged.

### Future-task notes

- The "failed tasks sort first, then new" ordering rule lives in plan.md
  prose and task_tracking.md; if the plan ever grows large, an explicit
  sort could be enforced by a convention or a tiny script. Not needed now.

### Tooling/process

- [open] The `spec/skills/work.md` workflow assumes a single
  session-at-a-time agent; a shared plan.md would need an "in progress"
  status if multiple sessions ever run concurrently. Deferred unless that
  happens.