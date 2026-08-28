# Task Tracking

Open tasks are stored in the `spec/docs/plan.md` document. A task is a
record with a `##` header (task name), a `Status:` line, a `Priority:`
line, the task body, and an optional `References:` line.

A task is `new` until it is done:

- `new` — not started (the default for a newly added task).

Priorities:

- `Priority: N` right after the `Status:` line; default `0` for new
  records. Higher numeric value = more important.
- `Priority: -1` = deferred: the task is not auto-picked until its
  priority is raised. To defer a task, set its priority to `-1`.

`done` is not a status in plan.md: a finished task's record is removed
from plan.md and archived into the report of the session that worked on it
(see `report_tracking.md`). A task leaves plan.md only when its work is
complete and committed.

Ad-hoc tasks requested directly by the user are not added to plan.md; they
are one-off work handled outside the plan and reported via
`report_tracking.md`.

## Adding a Task

- Add a `## {title}` record to plan.md, followed by `Status: new`, a
  `Priority: 0` line, the task body, and an optional `References:` line
  naming relevant ADRs.
- Append it at the end of plan.md; the owner edits `Priority:` values to
  set priority (no physical reordering needed).

## Choosing a Task

- Pick the highest-priority `new` record in plan.md; ties break by file
  order. Deferred records (`Priority: -1`) are never auto-picked.

## Finishing a Task

When a task is done:

1. Remove its record from plan.md.
2. Archive the record (header + body, with `Status: done`; the `Priority:`
   line is dropped) into the report file for the session — see
   `report_tracking.md`.

## When Work Is Blocked

If work on a task cannot proceed (missing prerequisite, the task's
assumption is wrong, an owner decision is needed), present the situation
to the user and continue per their direction. Do not write failure files
and do not change the task's status: the task stays `new`. The user may
re-scope or drop the record.