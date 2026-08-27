# unicaptcha

Universal Python interface to multiple anti-captcha services.

**Status: highly experimental.** Pre-1.0. No public API stability is promised, even for the documented surface. Anything may change between releases.

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
verification of their JSON API (ADR-0071).

## Supported CAPTCHA kinds (v1)

- Image CAPTCHA (`bytes` or `Path`)
- Text CAPTCHA (plain-text question)
- reCAPTCHA v2 (checkbox and invisible; Enterprise via flags)
- reCAPTCHA v3 (Enterprise via flags)
- hCaptcha (invisible via flag)
- FunCaptcha / Arkose
- GeeTest v3
- GeeTest v4

## Install

```
uv add unicaptcha
```

Requires Python 3.11+. Single runtime dependency: `httpx`.

## Usage sketch

The exact API is being finalized; the intended shape:

```python
from pathlib import Path

from unicaptcha import Solver, ImageChallenge
from unicaptcha.providers.twocaptcha import TwoCaptchaAdapter

client = Solver(adapters=[TwoCaptchaAdapter("...")])
result = client.solve(ImageChallenge(Path("test.png")))
print(result.solution.text)
```

Kind-base challenges carry universal fields only and route to any
registered adapter supporting the kind (`provider="capmonster"` to pin
one, uniform random choice when omitted); provider-specific options
use the concrete class, e.g. `TwoCaptchaImageChallenge(body=..., numeric=True)`
(ADR-0064). Image `body` accepts `bytes` or `Path` (ADR-0065).

Two-phase batch workflows split submit from collection (ADR-0067):

```python
ticket = client.submit(ImageChallenge(Path("a.png")))   # collect later
...
result = client.wait(ticket)                            # -> TaskResult, typed
status = client.wait_ref(TaskRef("twocaptcha", 12345), timeout=120)  # from persisted ids
```

An async-native `AsyncSolver` and per-provider facade clients
(`TwoCaptchaClient` and async counterpart) are part of the same design.
See `spec/docs/architecture.md` for the complete specification.

## Custom providers

unicaptcha ships a public adapter SDK: third parties can implement their own
provider adapters and register them in the universal client. See
`spec/docs/architecture.md` ("Adapter SDK") for the contract.

## Funding

The built-in adapters embed unicaptcha's referral ID in every request by
default; the provider pays the project a small commission per solve at no
change to your pricing. Pass `referral=False` to disable it, or
`referral="your-own-id"` to credit your own software registration
(ADR-0072). Third-party adapters embed nothing by default.

## License

MIT. Repository: https://github.com/lorien/unicaptcha
