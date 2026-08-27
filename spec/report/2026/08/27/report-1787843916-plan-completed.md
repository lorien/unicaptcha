## Report on task: remove var/plan.completed handling

### Done

- `spec/skills/work.md`: dropped the `## When no more tasks to do`
  section. The workflow now simply ends when there is nothing to do; no
  `var/plan.completed` marker file is created.
- No physical `var/plan.completed` file existed (verified).

### Future-task notes

- `agent-bootstrap.md` (generic workflow prompt, untouched per owner):
  the earlier draft plan included a "completion signal" example
  (`var/plan.completed`); drop it when that file is finally updated.

### Tooling/process

- Historical report `report-1787830211-task-tracking-redesign.md` line 22
  still says `var/plan.completed` is "unchanged"; left as-is (historical
  records are not rewritten for later workflow changes).