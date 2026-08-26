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

## Done

- `unicaptcha/events.py`: `TaskEventKind` enum (7 values, ADR-0018) and
  frozen `TaskEvent` dataclass (`kind`, `provider`, `elapsed`, `attempt`
  required; `task_id`/`detail`/`error_kind` default `None`). Public
  handler aliases `SyncEventHandler` / `AsyncEventHandler`.
- `unicaptcha/_internal/handlers.py` (option A, approved by owner): the
  ADR-0018 machinery shared by the future clients —
  `check_sync_handler` (rejects coroutine functions at attachment with
  `InvalidConfigError`, unwrapping `functools.partial` chains),
  `emit_sync` (inline call; awaitable result from a pathological wrapper
  is WARNING-logged on the flat `unicaptcha` logger and discarded),
  `emit_async` (inline call, awaits awaitable results). Handler errors
  propagate raw on both tiers. Constructor/per-call attachment wiring
  lands with clients (tasks 9/10).
- Root `__init__.py` re-exports `TaskEvent` / `TaskEventKind` (ADR-0036).
- Tests (98 total passing): enum values/order, `TaskEvent` fields/frozen/
  defaults, data-driven `error_kind` matrix pinning the ADR-0018
  terminal-failure kind sets (and `None` on non-failure kinds), sync
  guard (plain/partial coroutine-function rejection), dispatch behavior
  (awaitable discard + WARNING via caplog, error propagation both tiers,
  `None` no-ops), root exports.
- Full suite green (ruff, mypy strict, pyright strict, slotscheck, pytest).
  No hard-coded credentials.