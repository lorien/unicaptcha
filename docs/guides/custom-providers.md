# Custom providers

unicaptcha ships a public **adapter SDK**: third parties can implement
their own provider adapters and register them in the universal client.

## The two base classes

- **`BaseAdapter`** — the abstract contract every adapter implements.
  It declares the provider's identity (`provider`, `challenges`,
  `default_base_url`) and the translation methods (`build_payload`,
  `parse_submit_response`, `parse_task_status`, `parse_balance`,
  `map_provider_error`).
- **`AntiCaptchaCompatAdapterBase`** — the shared implementation base for
  adapters speaking the Anti-Captcha-compatible
  `createTask`/`getTaskResult` JSON protocol (2Captcha's modern JSON API,
  Anti-Captcha, CapMonster Cloud, Capsolver, and compatible mirrors).
  Subclasses declare `json_provider`, `error_kinds`,
  `unknown_task_codes`, and implement `_build_task`/`_solution_from`.
  Third-party providers using that protocol inherit the whole
  response-parsing pipeline.

## What an adapter does

Adapters are pure translators: they build request payloads, parse
provider responses, and map provider errors into the library's error
hierarchy. They perform **no network I/O themselves** — the engine owns
transport and retries.

## Minimal example

```python
from typing import ClassVar

from unicaptcha.adapter import AntiCaptchaCompatAdapterBase
from unicaptcha.challenge.image import ImageChallenge
from unicaptcha.errors import ErrorKind

class MyServiceAdapter(AntiCaptchaCompatAdapterBase):
    provider: ClassVar[str] = "myservice"
    json_provider: ClassVar[str] = "myservice"
    default_base_url: ClassVar[str] = "https://api.myservice.com"
    challenges = frozenset({MyServiceImageChallenge})
    error_kinds = {"ERROR_BAD_KEY": ErrorKind.AUTHENTICATION}
    unknown_task_codes = frozenset({"ERROR_TASK_NOT_FOUND"})

    def _build_task(self, challenge):
        return {"type": "ImageToTextTask", "body": challenge.body_b64}

    def _solution_from(self, solution):
        return MyServiceImageSolution(solution["text"])
```

## Registering

```python
from unicaptcha import Solver

client = Solver(adapters=[MyServiceAdapter("YOUR_API_KEY")])
```

Anything that is not a `BaseAdapter` raises `TypeError` at construction;
the same provider string twice raises `ValueError`.

## Reference pattern

The test suite ships a complete reference third-party adapter,
`MyServiceAdapter` (`tests/_myservice.py`), written against the public
API only — the pattern to follow.

- [Adapter SDK reference](../api/adapter.md)
- [Errors](errors.md) — mapping provider codes to `ErrorKind`