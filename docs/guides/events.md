# Events

Pass `on_event=` to observe the task lifecycle as typed `TaskEvent`s.
The handler receives one event per lifecycle step and can be set at
construction or per call.

```python
def on_event(event: TaskEvent) -> None:
    print(event.kind.name, event.task_id, event.error_kind)

client = Solver(adapters=[...], on_event=on_event)
```

Async clients use the same shape with `AsyncSolver`/`Async…Client`; the
handler may be a plain function or an awaitable.

## Event kinds

| `TaskEventKind` | When |
|---|---|
| `PRE_FLIGHT_FAILED` | Routing failed before any network traffic. |
| `SUBMIT_REQUESTED` | A `createTask` attempt is about to be sent. |
| `SUBMIT_ACCEPTED` | `createTask` returned a task id. |
| `SUBMIT_FAILED` | The submit ultimately failed. |
| `RESULT_REQUESTED` | A `getTaskResult` poll is about to be sent. |
| `RESULT_RECEIVED` | The result was received and solved. |
| `RESULT_FAILED` | Polling ended in failure (no solution, timeout, …). |

## Event fields

A `TaskEvent` carries:

| Field | Meaning |
|---|---|
| `kind` | The `TaskEventKind`. |
| `provider` | Provider string of the adapter involved. |
| `elapsed` | Time since the operation started (`timedelta`). |
| `attempt` | 1-based attempt number. |
| `task_id` | Task id once known (else `None`). |
| `detail` | Free-form detail (e.g. the provider error text). |
| `error_kind` | `ErrorKind` on failure events (else `None`). |

## Example

```python
from unicaptcha import ErrorKind, Solver, TaskEventKind
from unicaptcha.provider.twocaptcha import TwoCaptchaAdapter

seen: list[str] = []


def on_event(event) -> None:
    seen.append(event.kind.name)


with Solver(
    adapters=[TwoCaptchaAdapter("YOUR_API_KEY")],
    on_event=on_event,
) as client:
    client.solve_image(b"captcha.png")

assert "SUBMIT_ACCEPTED" in seen
assert "RESULT_RECEIVED" in seen
```

## Reference

- [`TaskEvent`, `TaskEventKind`](../api/events.md)

## Usage statistics

A `StatsCollector` turns the same `on_event` stream into cumulative
solve/failure counters and elapsed time, per provider — no client state:

```python
from unicaptcha import Solver, StatsCollector
from unicaptcha.provider.twocaptcha import TwoCaptchaAdapter

collector = StatsCollector()
with Solver(
    adapters=[TwoCaptchaAdapter("YOUR_API_KEY")],
    on_event=collector.on_event,
) as client:
    client.solve_image(b"captcha.png")

stats = collector.snapshot()
print(stats.solved, stats.failed, stats.per_provider)
```

- `snapshot()` returns an immutable `UsageStats` (`solved`, `failed`,
  `elapsed`, per-provider breakdown, and `cost_totals` keyed by currency);
  `reset()` zeroes it.
- The collector is synchronous, so the same handler works with
  `AsyncSolver` / `Async…Client`.
- Classification follows the terminal events: `RESULT_RECEIVED` counts
  as solved (and adds its `cost`); `PRE_FLIGHT_FAILED` / `SUBMIT_FAILED`
  / `RESULT_FAILED` count as failed.
- Cost totals are currency-safe: each provider instance has one currency
  (per-service default, e.g. `api.rucaptcha.com` → RUB, others USD), so
  `per_provider.cost` sums one currency, and `cost_totals` groups by
  currency code — never a blind cross-currency sum.

See [`StatsCollector`, `UsageStats`](../api/stats.md).