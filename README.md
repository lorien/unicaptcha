# unicaptcha

Universal Python interface to multiple anti-captcha services.

**Status: highly experimental.** Pre-1.0. No public API stability is promised, even for the documented surface. Anything may change between releases.

## Supported services

| Provider | Kind string | Default base URL |
|---|---|---|
| 2Captcha (modern JSON API) | `twocaptcha` | `https://api.2captcha.com` |
| Anti-Captcha | `anti-captcha` | `https://api.anti-captcha.com` |
| CapMonster Cloud | `capmonster` | `https://api.capmonster.cloud` |

2Captcha-protocol mirrors such as RuCaptcha work by overriding the 2Captcha adapter's base URL.

## Supported CAPTCHA kinds (v1)

- Image CAPTCHA (raw `bytes`)
- Text CAPTCHA (plain-text question)
- reCAPTCHA v2 (checkbox and invisible)
- reCAPTCHA v3
- hCaptcha

## Install

```
uv add unicaptcha
```

Requires Python 3.11+. Single runtime dependency: `httpx`.

## Usage sketch

The exact API is being finalized; the intended shape:

```python
from unicaptcha import MultiClient, SecretStr
from unicaptcha.providers.twocaptcha import (
    TwoCaptchaAdapter,
    TwoCaptchaImageChallenge,
)

client = MultiClient(adapters=[TwoCaptchaAdapter(api_key=SecretStr("..."))])
result = client.solve(TwoCaptchaImageChallenge(body=image_bytes))
print(result.solution.text)
```

An async-native `AsyncMultiClient` and per-provider facade clients
(`TwoCaptchaClient` and async counterpart) are part of the same design.
See `spec/ref/architecture.md` for the complete specification.

## Custom providers

unicaptcha ships a public adapter SDK: third parties can implement their own
provider adapters and register them in the universal client. See
`spec/ref/architecture.md` ("Adapter SDK") for the contract.

## License

MIT. Repository: https://github.com/lorien/unicaptcha
