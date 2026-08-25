# Task 3: Error hierarchy

Status: new

Implement `unicaptcha/errors.py`:

- `UnicaptchaError` base with `kind: ErrorKind` and `raw_response: bytes`,
  plus the hierarchy: `NetworkError`, `AuthenticationError`,
  `InsufficientBalanceError`, `UnsupportedChallengeError`,
  `InvalidChallengeError`, `TaskTimeoutError`, `RateLimitError`,
  `ServiceBusyError`, `NoSolutionError`, `InvalidConfigError`,
  `ClientClosedError`, `ProviderError` (+ `EmptySolutionError`).
- `ErrorKind` enum (13 values).
- Chaining discipline (`raise ... from cause`); no `provider_code`
  attribute; no `SolveCancelledError`, no `UnknownTaskError`.
- Wrong-provider routing raises `TypeError` pre-flight, no network.

References: ADR-0009, ADR-0040, ADR-0057, ADR-0058, ADR-0059, ADR-0045.