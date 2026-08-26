## Workflow

Study documents inside `spec/ref/` directory, this is collection of documents
describing the current project.
Read `spec/skill/task_tracking.md`.
If user has not instructed you on what task to work, then
select one task yourself and work on it.
After task is done do these aciton (in this very order):
- perform final checks (see below)
- create new report file, see the section "Report" below
- make a new github commit, in commit message describe what you have done

Do not do github commit and do not create report file if you have not worked on any task
    from implementation plan (like when all tasks are in "done" state).

## Task Work Final List

1. Run the test suite and checks described in `spec/ref/testing.md`,
   and fix anything they surface.
2. Ensure the security credentials are not hard-coded

## Report

Based on result of working session, compile a list of suggestions about how to change project environment, spec, tools, etc to help you build
things more effectively. Save this suggestions into new file in `spec/report/<year>/<month>/<day>/` directory.

Filename: `report-<epoch>-task-<N>.md` for an indexed implementation task,
`report-<epoch>-<slug>.md` for ad-hoc work requested directly by the user.

First line of report must be `## Report on task <task number>: <task title>`.
For ad-hoc work (not an indexed task), use
`## Report on task: <descriptive title>` instead. The second line must be
`State: new`.

Structure the suggestions under these categories, each item prefixed with
a status marker:

- `### Spec/ADR amendments` — spec/doc/ADR changes suggested.
- `### Future-task notes` — reminders for work that later tasks must do.
- `### Tooling/process` — environment, toolchain, or workflow learnings.

Item markers: `[open]` not yet addressed, `[acted]` already handled
(append a one-line note), `[needs-decision]` requires an owner decision.

After writing the report, refresh `spec/report/open.md`: the roll-up of
every still-`[open]` / `[needs-decision]` item across all reports (one
line per item: category, task ref, one-liner, link to the source report).

## When task failed

If in process of working on the task, you have decied it can not be done, write short explanation
    of what failed and why to the file `var/task.failed`.

## When no more tasks to do

If you choose tasks to work automatically and there is no more tasks to do,
then create the empty file `var/plan.completed`.
