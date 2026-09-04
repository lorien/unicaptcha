# unicaptcha

Universal Python interface to multiple anti-captcha services. One typed
API over 2Captcha, Anti-Captcha, CapMonster Cloud, and Capsolver — async
and blocking.

**Status: highly experimental.** Pre-1.0. No public API stability is
promised, even for the documented surface. Anything may change between
releases.

## What it does

Send a captcha challenge to the client and receive a typed, solved
result:

```python
from pathlib import Path

from unicaptcha import Solver, ImageChallenge
from unicaptcha.provider.twocaptcha import TwoCaptchaAdapter

with Solver(adapters=[TwoCaptchaAdapter("YOUR_API_KEY")]) as client:
    result = client.solve(ImageChallenge(Path("captcha.png")))
    print(result.solution.text)
```

The client handles the submit → poll → result lifecycle, retries with
backoff, total-time budgets, error normalization, and events.

## Features

- **Universal client** (`Solver` / `AsyncSolver`) — register several
  providers, dispatch each challenge to one that supports it.
- **Provider facades** (`TwoCaptchaClient`, `AntiCaptchaClient`,
  `CapMonsterClient`, `CapsolverClient` + async twins) — one
  convenience method per captcha kind for a single provider.
- **Nine captcha kinds** — image, text, reCAPTCHA v2, reCAPTCHA v3,
  hCaptcha, FunCaptcha/Arkose, GeeTest v3, GeeTest v4, Cloudflare
  Turnstile.
- **Typed throughout** — frozen dataclass challenges, typed results,
  exact `Decimal` costs, strict mypy/pyright annotations.
- **Sync + async as peers** — a fully async-native engine and a
  blocking engine; no wrapper magic in either direction.
- **Predictable failures** — one exception hierarchy with a normalized
  `ErrorKind`, verbatim provider responses preserved.
- **Adapters** — third-party providers via a public adapter SDK.

## Supported providers

| Provider | Kind string | Default base URL |
|---|---|---|
| 2Captcha (modern JSON API) | `twocaptcha` | `https://api.2captcha.com` |
| Anti-Captcha | `anti-captcha` | `https://api.anti-captcha.com` |
| CapMonster Cloud | `capmonster` | `https://api.capmonster.cloud` |
| Capsolver | `capsolver` | `https://api.capsolver.com` |

2Captcha-protocol mirrors such as RuCaptcha work by overriding the base
URL (RuCaptcha's JSON API v2 is verified complete):
`TwoCaptchaClient(api_key=..., base_url="https://rucaptcha.com")`.

## Supported CAPTCHA kinds

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

## Project links

- [Getting started](getting-started.md)
- [API Reference](api/index.md)
- Source: <https://github.com/lorien/unicaptcha>
- License: MIT