# Task 4: Events

Status: new

Implement `unicaptcha/events.py`:

- `TaskEventKind` enum and `TaskEvent` dataclass: `kind`, `provider`,
  `task_id`, `elapsed`, `attempt`, `detail`, `error_kind` (with the
  per-kind value matrix and the terminal-event invariant).
- `on_event` handler attachment: constructor + per-call (all-or-nothing
  override); sync tier `Callable[[TaskEvent], None]` with coroutine
  rejection and awaitable-discard WARNING; async tier awaited inline.
- Handler errors propagate raw.

References: ADR-0018, ADR-0039, ADR-0044, ADR-0067, ADR-0075.