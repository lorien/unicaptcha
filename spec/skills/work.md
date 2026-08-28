## Workflow

Study documents inside `spec/docs/` directory, this is collection of documents
describing the current project.
Read `spec/skills/task_tracking.md`.
Read `spec/skills/report_tracking.md`.
The user may give you an ad-hoc task directly (work not listed in
`spec/docs/plan.md`). If the user has not instructed you on what task to
work, select one yourself from `spec/docs/plan.md` (the highest-priority
`new` task; deferred tasks with `Priority: -1` are not picked)
and work on it.
Before implementing a task, present your implementation plan and wait
for the owner's approval.
After task is done do these aciton (in this very order):
- perform final checks (see below)
- create new report file (see `report_tracking.md`); for a task taken from
  `spec/docs/plan.md`, the report archives its record
- if the task came from `spec/docs/plan.md`, remove its record from the plan
- make a new github commit, in commit message describe what you have done

Do not do github commit and do not create report file if you have not worked
on any task to completion (like when there is no work to do).

## Task Work Final List

1. Run the test suite and checks described in `spec/docs/testing.md`,
   and fix anything they surface.
2. Ensure the security credentials are not hard-coded


## When work is blocked

If work on a task cannot proceed (missing prerequisite, wrong assumption,
owner decision needed), present the situation to the user and continue per
their direction. Do not write any failure files and do not change the
task's status; a task leaves `spec/docs/plan.md` only when its work is
complete and committed.