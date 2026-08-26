## Workflow

Study documents inside `spec/ref/` directory, this is collection of documents
describing the current project.
Read `spec/skills/task_tracking.md`.
Read `spec/skills/report_tracking.md`.
If user has not instructed you on what task to work, then
select one task yourself and work on it.
After task is done do these aciton (in this very order):
- perform final checks (see below)
- create new report file
- make a new github commit, in commit message describe what you have done

Do not do github commit and do not create report file if you have not worked on any task
    from implementation plan (like when all tasks are in "done" state).

## Task Work Final List

1. Run the test suite and checks described in `spec/ref/testing.md`,
   and fix anything they surface.
2. Ensure the security credentials are not hard-coded


## When task failed

If in process of working on the task, you have decied it can not be done, write short explanation
    of what failed and why to the file `var/task.failed`.

## When no more tasks to do

If you choose tasks to work automatically and there is no more tasks to do,
then create the empty file `var/plan.completed`.
