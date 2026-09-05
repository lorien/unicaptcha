# Examples

Runnable scripts live in the repository at `examples/sync/` and
`examples/async/`, one per use case, in blocking and asyncio-native
flavors.

## Policy

The examples demonstrate the **2Captcha** provider. Anti-Captcha,
CapMonster Cloud, and Capsolver work exactly the same way: swap
`TwoCaptchaClient` for `AntiCaptchaClient`, `CapMonsterClient`, or
`CapsolverClient` (or their async twins) and adjust per-provider extras.

## Running

Every script needs a real API key and solves real captchas (credits are
deducted):

```
export UNICAPTCHA_TWOCAPTCHA_API_KEY=your_api_key
python examples/sync/recaptcha_v2.py
python examples/async/turnstile.py
```

Without the key a script prints how to set it and exits non-zero —
nothing is submitted. Demo sitekeys are public 2Captcha demo pages (plus
official hCaptcha/Arkose test keys), so the scripts run as-is once the
key is set.

> **Illustrative examples:** `geetest_v3.py` and `funcaptcha.py` are
> illustrative — the GeeTest v3 demo `challenge` is single-use and
> Arkose's public demo blob is not worker-solvable, so those solves are
> expected to end in `NoSolutionError`.

## Index

| File (sync/ + async/) | Shows |
|---|---|
| `universal_client.py` | `Solver`/`AsyncSolver` multi-adapter dispatch |
| `auto_solve.py` | detect + auto-solve a page's captcha (`AutoSolveResult` / `fill`) |
| `image.py` | image captcha from `bytes` (uses `images/captcha.png`) |
| `text.py` | text question captcha |
| `recaptcha_v2.py` | reCAPTCHA v2 token |
| `recaptcha_v3.py` | reCAPTCHA v3 token with `action`/`min_score` |
| `hcaptcha.py` | hCaptcha token |
| `funcaptcha.py` | FunCaptcha/Arkose token |
| `geetest_v3.py` | GeeTest v3 challenge/validate/seccode |
| `geetest_v4.py` | GeeTest v4 (captcha_id) |
| `turnstile.py` | Cloudflare Turnstile token |
| `two_phase.py` | `submit()`/`wait()` batch with `TaskTicket` |
| `aux_ops.py` | balance, task status, good/bad reports |
| `events.py` | `on_event` task-lifecycle stream |
| `errors.py` | exception handling and `ErrorKind` |
| `proxy.py` | proxy on a challenge |