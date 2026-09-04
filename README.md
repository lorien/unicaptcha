# unicaptcha

Universal Python interface to multiple anti-captcha services.

**Status: highly experimental.** Pre-1.0. No public API stability is promised, even for the documented surface. Anything may change between releases.

Documentation: https://lorien.github.io/unicaptcha/

## Supported services

| Provider | Kind string | Default base URL |
|---|---|---|
| 2Captcha (modern JSON API) | `twocaptcha` | `https://api.2captcha.com` |
| Anti-Captcha | `anti-captcha` | `https://api.anti-captcha.com` |
| CapMonster Cloud | `capmonster` | `https://api.capmonster.cloud` |
| Capsolver | `capsolver` | `https://api.capsolver.com` |

2Captcha-protocol mirrors such as RuCaptcha work by overriding the base URL
(RuCaptcha's JSON API v2 is verified complete): `TwoCaptchaClient(api_key=...,
base_url="https://rucaptcha.com")`. Smaller mirrors need per-service
verification of their JSON API.

## Supported CAPTCHA kinds (v1)

| Kind | Challenge base | Solution base |
|---|---|---|
| Image CAPTCHA | `ImageChallenge` | `ImageSolution` |
| Text CAPTCHA | `TextChallenge` | `TextSolution` |
| reCAPTCHA v2 | `RecaptchaV2Challenge` | `RecaptchaV2Solution` |
| reCAPTCHA v3 | `RecaptchaV3Challenge` | `RecaptchaV3Solution` |
| hCaptcha | `HCaptchaChallenge` | `HCaptchaSolution` |
| FunCaptcha / Arkose | `FunCaptchaChallenge` | `FunCaptchaSolution` |
| GeeTest v3 | `GeeTestV3Challenge` | `GeeTestV3Solution` |
| GeeTest v4 | `GeeTestV4Challenge` | `GeeTestV4Solution` |
| Cloudflare Turnstile | `TurnstileChallenge` | `TurnstileSolution` |

Kind coverage varies by provider (e.g. text is 2Captcha + Anti-Captcha
only); unsupported kinds raise `UnsupportedChallengeError`.

## Install

```
uv add unicaptcha
```

Requires Python 3.11+. Single runtime dependency: `httpx`.

## Usage

### Universal client

The universal client registers one or more provider adapters and dispatches
each challenge to the adapter that supports it.

```python
from pathlib import Path

from unicaptcha import Solver, ImageChallenge
from unicaptcha.provider.twocaptcha import TwoCaptchaAdapter

client = Solver(adapters=[TwoCaptchaAdapter("YOUR_API_KEY")])
result = client.solve(ImageChallenge(Path("captcha.png")))
print(result.solution.text)   # the solved captcha text
```

A challenge is a frozen dataclass describing what to solve. The kind-base
classes (`ImageChallenge`, `RecaptchaV2Challenge`, …) carry only the fields
every provider shares; the concrete provider classes
(`TwoCaptchaImageChallenge`, …) add provider-specific options.

- A kind-base challenge routes to any registered adapter supporting the
  kind — pass `provider="twocaptcha"` to pin one, or omit it for a uniform
  random pick among the supporting adapters.
- Provider extras use the concrete class, e.g.
  `TwoCaptchaImageChallenge(body, numeric=True, min_len=4)`.
- Image bodies accept `bytes` or a `Path`; the value is normalized to bytes
  at construction.

### Provider facades

For a single provider, a facade client offers one convenience method per
kind with full parameter parity:

```python
import asyncio

from unicaptcha.provider.twocaptcha import AsyncTwoCaptchaClient, TwoCaptchaClient

with TwoCaptchaClient("YOUR_API_KEY") as client:
    result = client.solve_image(b"captcha.png", numeric=1)


async def main() -> None:
    async with AsyncTwoCaptchaClient("YOUR_API_KEY") as client:
        result = await client.solve_recaptcha_v2(
            sitekey="SITEKEY", pageurl="https://example.com"
        )
        print(result.solution.token)


asyncio.run(main())
```

Each provider package exports `<Provider>Client` and `Async<Provider>Client`
(`TwoCaptchaClient`, `AntiCaptchaClient`, `CapMonsterClient`,
`CapsolverClient`, and their async counterparts). Facade constructors take
`api_key` positionally and otherwise mirror `Solver` minus `adapters`
(`base_url`, `referral`, `proxy`, `time`, `retry`, `network`, `on_event`).

### Two-phase batch

`submit()` splits solving from collecting: it returns a `TaskTicket`, which
you can persist (via its `task_ref`) and collect later.

```python
from unicaptcha import ImageChallenge, TaskRef

ticket = client.submit(ImageChallenge(Path("a.png")))   # collect later
# ... later ...
result = client.wait(ticket)                            # -> TaskResult, typed
status = client.wait_ref(TaskRef("twocaptcha", 12345), timeout=120)  # from a persisted id
```

### Auxiliary operations

The universal client and the facades share the same aux names:

- `get_balance(provider)` → `Decimal` balance in USD (facades take no argument)
- `get_task_status(task)` → one-shot status (`TaskRef`, or `int` on facades)
- `report_bad_result(task)` / `report_good_result(task)` → `bool`
  (coverage varies by provider)
- `get_abandoned_tasks()` → tasks cancelled while solving

### Errors

Every library exception derives from `UnicaptchaError` and carries a
`kind: ErrorKind` plus the verbatim provider response in `raw_response`:
`NoSolutionError`, `TaskTimeoutError`, `RateLimitError`, `ServiceBusyError`,
`InsufficientBalanceError`, `AuthenticationError`, `NetworkError`,
`ProviderError`, `InvalidConfigError`, `InvalidChallengeError`,
`UnsupportedChallengeError`, `ClientClosedError`.

### Events

Pass `on_event=` at construction or per call to observe the task lifecycle
(`SUBMIT_REQUESTED`, `SUBMIT_ACCEPTED`, `RESULT_RECEIVED`, …) as typed
`TaskEvent`s.

## Examples

Runnable scripts, one per use case in `examples/sync/` and `examples/async/`:
every captcha kind, two-phase batch, aux ops, events, errors, proxy.
See [examples/README.md](examples/README.md).

## Custom providers

unicaptcha ships a public adapter SDK: third parties can implement their own
provider adapters (`BaseAdapter`) and register them in the universal client.
The test suite includes a reference third-party adapter, `MyServiceAdapter`
(`tests/_myservice.py`), written against the public API only — the pattern to
follow. See `spec/docs/architecture.md` ("Adapter SDK") for the contract.

## Funding

The built-in adapters embed unicaptcha's referral ID in every request by
default; the provider pays the project a small commission per solve at no
change to your pricing. Pass `referral=False` to disable it, or
`referral="your-own-id"` to credit your own software registration.
Third-party adapters embed nothing by default.

## License

MIT. Repository: https://github.com/lorien/unicaptcha