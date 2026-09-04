# Universal client

`Solver` (blocking) and `AsyncSolver` (asyncio-native) register one or
more provider adapters and dispatch each challenge to the adapter that
supports it.

## Construction

```python
from unicaptcha import Solver
from unicaptcha.provider.twocaptcha import TwoCaptchaAdapter
from unicaptcha.provider.capmonster import CapMonsterAdapter

client = Solver(
    adapters=[TwoCaptchaAdapter("2CAPTCHA_KEY"), CapMonsterAdapter("CAPMONSTER_KEY")],
    # optional: time=..., retry=..., network=..., proxy=..., on_event=...
)
```

- Adapters are keyed by their `provider` string; registering the same
  provider twice raises `ValueError`.
- The adapter list must not be empty.
- `Solver` and `AsyncSolver` are context managers: `close()` /
  `await aclose()` release the underlying HTTP transport.

## Solving

```python
result = client.solve(ImageChallenge(Path("a.png")))
# or pin a provider:
result = client.solve(ImageChallenge(Path("a.png")), provider="twocaptcha")
```

- `provider=` accepts a provider string, an adapter instance, or an
  adapter class.
- With `provider=None`, the client picks uniformly at random among the
  registered adapters that support the challenge kind.
- `time=`, `retry=`, and `on_event=` may be passed per call as well.

The async twin is identical:

```python
async with AsyncSolver(adapters=[...]) as client:
    result = await client.solve(RecaptchaV2Challenge(sitekey="...", pageurl="..."))
```

## Auxiliary operations

The universal client exposes the same aux operations as the facades:

- `get_balance(provider)` → `Decimal` balance in USD. `provider` may be
  a string, adapter instance, or adapter class.
- `get_task_status(ref)` → one-shot status for a `TaskRef`.
- `report_bad_result(ref)` / `report_good_result(ref)` → `bool`
  (coverage varies by provider).
- `get_abandoned_tasks()` → tasks that were cancelled while solving.

## Two-phase solving

`submit()` separates solving from collecting and returns a `TaskTicket`;
`wait()` collects the result later. See
[Two-phase batch](two-phase.md).

## Error handling

Wrong-provider routing raises `TypeError` pre-flight (no network
traffic); unsupported kinds raise `UnsupportedChallengeError`. See
[Errors](errors.md).

## Reference

- [`Solver` / `AsyncSolver` API](../api/clients.md)
- [Configuration](configuration.md)
- [Proxy](proxy.md)
- [Events](events.md)