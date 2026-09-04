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