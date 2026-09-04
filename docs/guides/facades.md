# Provider facades

For a single provider, a facade client offers one convenience method per
kind with full parameter parity. Each provider package exports
`<Provider>Client` and `Async<Provider>Client`:

- `TwoCaptchaClient` / `AsyncTwoCaptchaClient`
- `AntiCaptchaClient` / `AsyncAntiCaptchaClient`
- `CapMonsterClient` / `AsyncCapMonsterClient`
- `CapsolverClient` / `AsyncCapsolverClient`

## Construction

Facade constructors mirror `Solver` minus `adapters`:

```python
from unicaptcha.provider.twocaptcha import TwoCaptchaClient

client = TwoCaptchaClient(
    "YOUR_API_KEY",
    base_url=None,     # override for mirrors (e.g. RuCaptcha)
    referral=True,     # embed the project's affiliate id (see Funding)
    proxy=None,        # default proxy for challenges that carry one
    time=None,         # TimeConfig
    retry=None,        # RetryConfig
    network=None,      # NetworkConfig
    on_event=None,
)
```

## Solving

```python
from unicaptcha.provider.twocaptcha import TwoCaptchaClient

with TwoCaptchaClient("YOUR_API_KEY") as client:
    result = client.solve_image(b"captcha.png", numeric=1)
```

Async is a peer:

```python
import asyncio

from unicaptcha.provider.twocaptcha import AsyncTwoCaptchaClient


async def main() -> None:
    async with AsyncTwoCaptchaClient("YOUR_API_KEY") as client:
        result = await client.solve_recaptcha_v2(
            sitekey="SITEKEY", pageurl="https://example.com"
        )
        print(result.solution.token)


asyncio.run(main())
```

## Method surface

Each facade exposes one `solve_<kind>` method per supported kind
(`solve_image`, `solve_text`, `solve_recaptcha_v2`,
`solve_recaptcha_v3`, `solve_hcaptcha`, `solve_funcaptcha`,
`solve_geetest_v3`, `solve_geetest_v4`, `solve_turnstile`) plus the aux
operations shared with the universal client (`get_balance`,
`get_task_status`, `report_bad_result`, `report_good_result`,
`get_abandoned_tasks`).

On facades, `get_task_status`/`report_*` take a task id (`int | str`)
rather than a `TaskRef`; `get_balance` takes no argument.

## Reference

- [API Reference: Providers](../api/providers.md)
- [Two-phase batch](two-phase.md)
- [Configuration](configuration.md)