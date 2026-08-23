## Workflow

Study documents inside `spec/ref/` directory.
Read `spec/ref/research.md` document.
Read `spec/skill/task_tracking.md`.
Select ONLY ONE task and work on it.
After task is done do these aciton (in this very order):
- perform final checks (see below)
- create new report file, see the section "Report" below
- make a new github commit, in commit message describe what you have done

Do not do github commit and do not create report file if you have not worked on any task
    from implementation plan (like when all tasks are in "done" state).

## Task Done Check List

1. Ensure code is clean and correctly formatted
2. Ensure the security credentials are not hard-coded

## Report

Based on result of working session, compile a list of suggestions about how to change project environment, spec, tools, etc to help you build
things more effectively. Save this suggestions into new file in `spec/report/` directory. Give the file a name `report-N.md`, where N is next 
unused number, starting from 1. First line of report must be `## Report on task <task number>: <task title>`. The second line must be `State: new`.
Further lines must be actual suggestions you want to say.

## When task failed

If in process of working on the task, you have decied it can not be done, write short explanation
    of what failed and why to the file `var/task.failed`.

## When no more tasks to do

When there is no more tasks to do, create the empty file `var/plan.completed`.
