# Task Tracking

Open tasks are stored in the `spec/docs/plan.md` document. A task is a
record with a `##` header (task number + name), a `Status:` line, the task
body, and an optional `References:` line.

A task has exactly one of two statuses:

- `new` — not started (the default for a newly added task).
- `failed` — could not be completed as described; the record carries a
  `Reason:` line explaining why.

`done` is not a status in plan.md: a finished task's record is removed
from plan.md and archived into the report of the session that worked on it
(see `report_tracking.md`).

## Adding a Task

- Add a `## Task {N}: {title}` record to plan.md. For `{N}` use the first
  free number, starting from 1.
- Follow the header with `Status: new`, then the task body, then an
  optional `References:` line naming relevant ADRs.
- Failed tasks sort first, then new tasks; within a status, by task
  number — keep plan.md ordered accordingly.

## Choosing a Task

- Prefer a `failed` task over a `new` one.
- Among tasks in the same state, choose the lower task number.

## Finishing a Task

When a task is done:

1. Remove its record from plan.md.
2. Archive the record (header + body, with `Status: done`) into the
   report file for the session — see `report_tracking.md`.

## When a Task Fails

- In plan.md, change the record's status line to `Status: failed` and add
  a `Reason:` line with a short explanation of what failed and why.
- The record stays in plan.md until the task is re-opened (flip back to
  `new`, clear the reason) or dropped by the owner.