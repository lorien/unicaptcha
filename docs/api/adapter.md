# Adapter SDK

The public adapter contract. `BaseAdapter` is the abstract base every
adapter implements; `AntiCaptchaCompatAdapterBase` is the shared
implementation base for the Anti-Captcha-compatible
`createTask`/`getTaskResult` JSON protocol family; `Endpoints` declares
the request paths an adapter uses.

::: unicaptcha.adapter