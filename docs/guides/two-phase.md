# Two-phase batch

`submit()` splits solving from collecting: it returns a `TaskTicket`,
which you can persist (via its `task_ref`) and collect later.

```python
from pathlib import Path

from unicaptcha import ImageChallenge, TaskRef

ticket = client.submit(ImageChallenge(Path("a.png")))   # solve in background
# ... later ...
result = client.wait(ticket)                            # -> TaskResult, typed
```

## Persisted task ids

The task survives process restarts through its `TaskRef` — the
`(provider, task_id)` pair:

```python
status = client.wait_ref(TaskRef("twocaptcha", 12345), timeout=120)
```

`wait_ref` answers a `TaskStatusResult` and never raises on provider
outcomes: it returns `PENDING` when the budget is exhausted.

## Notes

- `TaskTicket` is not user-constructible; obtain it from
  `submit()`. Its `task_ref` and `submitted_at` are provenance from a
  real submission.
- Some providers answer the submit itself with an inline solution
  (the submit-ready fast path). In that case `wait()` returns
  immediately without polling.
- The same API exists on both tiers:
  `Solver.submit/wait/wait_ref` and `AsyncSolver.submit/wait/wait_ref`.

## Auxiliary status queries

- `get_task_status(ref)` — one-shot status (no polling).
- `get_abandoned_tasks()` — tasks that were submitted but never
  collected (e.g. cancelled while solving).

## Reference

- [`TaskTicket`, `TaskRef`, `TaskResult`, `TaskStatusResult`](../api/types.md)
- [Configuration](configuration.md) — `wait(timeout=...)` budgets