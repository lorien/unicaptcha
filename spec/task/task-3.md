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

## Done

- Completed `unicaptcha/errors.py` (base, `ErrorKind`, `InvalidConfigError`
  already landed in task 2): added `NetworkError`, `AuthenticationError`,
  `InsufficientBalanceError`, `UnsupportedChallengeError`,
  `InvalidChallengeError`, `TaskTimeoutError`, `RateLimitError`,
  `ServiceBusyError`, `NoSolutionError`, `ClientClosedError`,
  `ProviderError`, and `EmptySolutionError(ProviderError)` (ADR-0040).
- Every leaf has the explicit constructor `(message, *, raw_response=b"")`
  hardcoding its own kind, preserving the ADR-0009 1:1 invariant (class
  minus `Error` == SCREAMING_SNAKE `ErrorKind`).
- Module docstring documents the call-site disciplines: chaining
  (`raise ... from cause`), wrong-provider `TypeError` pre-flight
  (ADR-0045), and the absent `SolveCancelledError` / `UnknownTaskError`
  (ADR-0016/0050) — these are enforced in tasks 7-10, not in the classes.
- Root `__init__.py` re-exports all 13 error classes + `ErrorKind`
  (ADR-0036).
- Tests (80 total passing): data-driven 1:1 `ErrorKind`-to-class table test,
  hierarchy shape (`EmptySolutionError` under `ProviderError`; all leaves
  under `UnicaptchaError`), `raw_response` passthrough, absence guards for
  `SolveCancelledError`/`UnknownTaskError`, root exports.
- Full suite green (ruff, mypy strict, pyright strict, slotscheck, pytest).
  No hard-coded credentials.