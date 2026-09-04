# Getting started

## Install

```
uv add unicaptcha
```

or with pip:

```
pip install unicaptcha
```

Requires Python 3.11+. The only runtime dependency is `httpx`.

## Your first solve

Every provider requires an API key. This example uses the universal
client with the 2Captcha adapter:

```python
from pathlib import Path

from unicaptcha import Solver, ImageChallenge
from unicaptcha.provider.twocaptcha import TwoCaptchaAdapter

client = Solver(adapters=[TwoCaptchaAdapter("YOUR_API_KEY")])
result = client.solve(ImageChallenge(Path("captcha.png")))
print(result.solution.text)   # the solved captcha text
```

The same call is fully async with `AsyncSolver`:

```python
import asyncio
from pathlib import Path

from unicaptcha import AsyncSolver, ImageChallenge
from unicaptcha.provider.twocaptcha import TwoCaptchaAdapter


async def main() -> None:
    async with AsyncSolver(
        adapters=[TwoCaptchaAdapter("YOUR_API_KEY")]
    ) as client:
        result = await client.solve(ImageChallenge(Path("captcha.png")))
        print(result.solution.text)


asyncio.run(main())
```

## Challenges and solutions

A **challenge** is a frozen dataclass describing what to solve. The
kind-base classes (`ImageChallenge`, `RecaptchaV2Challenge`, …) carry
only the fields every provider shares; the concrete provider classes
(`TwoCaptchaImageChallenge`, …) add provider-specific options.

A **solution** is the typed result of a solve: `result.solution.text`
for image/text, `result.solution.token` for reCAPTCHA/hCaptcha/Turnstile
tokens, `challenge/validate/seccode` for GeeTest v3, and so on.

## Choosing a provider

- A kind-base challenge routes to **any registered adapter that
  supports the kind**. Omit `provider=` for a uniform random pick among
  the supporting adapters, or pass `provider="twocaptcha"` to pin one.
- Provider extras use the concrete class, e.g.
  `TwoCaptchaImageChallenge(body, numeric=True, min_len=4)`.
- Image bodies accept `bytes` or a `Path`; the value is normalized to
  bytes at construction.

## Next steps

- [Universal client](guides/universal-client.md)
- [Provider facades](guides/facades.md)
- [Configuration](guides/configuration.md)
- [Errors](guides/errors.md)
- [API Reference](api/index.md)