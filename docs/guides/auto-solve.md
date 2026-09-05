# Auto solve

Auto mode detects the captcha a page uses from its HTML source, solves
it, and tells you where to put the answer — no manual sitekey hunting.

## Detection

```python
from unicaptcha import detect

found = detect(html, "https://example.com/signup")
for item in found:
    print(item.kind, item.signals)
```

- `detect(html, pageurl)` returns the page's captchas as ready-to-solve
  challenges, in document order; `()` when there are none.
- `item.challenge` is a kind-base challenge (`RecaptchaV2Challenge`,
  `HCaptchaChallenge`, ...) you can pass straight to `solve()`.
- `item.kind` is a machine tag (`recaptcha-v2`, `recaptcha-v3`,
  `hcaptcha`, `turnstile`, `funcaptcha`, `geetest-v3`, `geetest-v4`);
  `item.signals` is the human-readable evidence that matched.
- Detection covers widget markup (`<div class="g-recaptcha">`, Turnstile
  `data-*` attributes, FunCaptcha `data-pkey`) and inline scripts
  (`grecaptcha.render/execute`, `hcaptcha.render`, `turnstile.render`,
  `initGeetest`, `initGeetest4`). Image/text captchas are API-driven and
  not detectable.
- `pageurl` is required: the solved token is bound to that domain.

## One-shot solving

```python
from unicaptcha import Solver
from unicaptcha.provider.twocaptcha import TwoCaptchaAdapter

with Solver([TwoCaptchaAdapter("2CAPTCHA_KEY")]) as client:
    auto = client.auto_solve(html, "https://example.com/signup")
```

`auto_solve` solves the first detected captcha and returns an
`AutoSolveResult`:

- `auto.result` — the usual typed `TaskResult` (`solution`, `cost`, ...).
- `auto.detected` — what was solved and why (kind, signals).
- `auto.fill` — a `{selector: value}` map for injecting the answers into
  the page's form:

| Kind | `fill` selectors |
|---|---|
| reCAPTCHA v2 / v3 | `#g-recaptcha-response` |
| hCaptcha | `textarea[name=h-captcha-response]` |
| Turnstile | `input[name=cf-turnstile-response]` |
| GeeTest v3 | `#geetest_challenge`, `#geetest_validate`, `#geetest_seccode` |
| GeeTest v4 | `#geetest_lot_number`, `#geetest_pass_token`, `#geetest_gen_time`, `#geetest_captcha_output` |
| FunCaptcha | empty (no injectable field — see below) |

Apply `fill` with your own browser layer:

```python
for selector, value in auto.fill.items():
    page.locator(selector).fill(value)
```

- No detection raises `NoCaptchaDetectedError` (an `ErrorKind`.
  `NO_CAPTCHA_DETECTED` error).
- `provider=` pins the solving provider, like `solve()`.
- FunCaptcha answers go through the page's Arkose callback, not a form
  field; `fill` is empty and `auto.result.solution.token` is what you
  hand to the callback.

## Several captchas on one page

`auto_solve` handles the common single-captcha case. For pages with
several, use `detect()` + `solve()` explicitly:

```python
found = detect(html, pageurl)
for item in found:
    result = client.solve(item.challenge)
```

## Reference

- [`detect`, `DetectedChallenge`, `AutoSolveResult` API](../api/detect.md)
- [Universal client](universal-client.md)
- [Errors](errors.md)