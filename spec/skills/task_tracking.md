# Task Tracking

The `spec/task/index.md` document contains list of all tasks and their states.
After you have done the task, update `spec/task/index.md`, change status of corresponding task to "done".
Also save brief list of things, you have done, into task file.

## Task Priority

When you decide which task to work next, consider these things:

- The "failed" tasks have priority higher than "new" tasks.
- Always choose "failed" task if there is such one.
- Among tasks of same state, chose the task with lower number.

## Task File

Details of the task are stored in `spec/task/task-{task number}.md` file. For `{task number}` use first free number, starting from 1.
Each task file starts with markdown header (title of the task), then description of the task.
Right after tasks's header there must be line with task's status in the form `Status: <new|failed|done>`.
Later, when task is done, its file might be appended with "Done:" section with a brief list of things have
been done durong the work on task.
After you created task file, add its reference to `spec/task/index.md` file, that must be new line in
form of ` - [<new|done>] {task number}: {task title}`.
So, for any task in `spec/task/index.md` you can get details from task file using the task number, specified in task index.
When status of task is changed, the "Status:" line in the task's file must be updated according to the new status of the task.


## When task is impossible to do

- If a task cannot be completed as described (missing prerequisite, reality contradicts the task, etc.),
    in task index, mark task state as "failed".
