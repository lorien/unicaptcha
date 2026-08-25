# Task 12: Anti-Captcha adapter + facade

Status: new

Implement `provider/anticaptcha/`:

- `challenge.py`: concrete challenge subclasses per ADR-0076 (nine kinds;
  text via API `TextCaptchaTask`; enterprise flags; min_score
  validation 0.5/0.7/0.9).
- `solution.py`: concrete solution subclasses (incl. `user_agent` /
  `resp_key` extras).
- `adapter.py`: `AntiCaptchaAdapter` — payload build + parse, error
  mapping, report pairs; proxy addresses IP-only (engine resolves
  hostname→IP async-safe, executor-backed; adapter stays pure).
- `client.py`: `AntiCaptchaClient` / `AsyncAntiCaptchaClient` facades.

References: ADR-0001, ADR-0007, ADR-0051, ADR-0061, ADR-0076, ADR-0041,
ADR-0040.