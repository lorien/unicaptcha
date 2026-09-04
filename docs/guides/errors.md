# Errors

Every library exception derives from `UnicaptchaError` and carries:

- `kind` — a normalized `ErrorKind` classification.
- `raw_response` — the verbatim provider response body (`bytes`) when
  one exists.

## Exception hierarchy

| Exception | `ErrorKind` | Meaning |
|---|---|---|
| `UnicaptchaError` | — | Base of the hierarchy. |
| `NetworkError` | `NETWORK` | Transport failure (DNS, refused, TLS, timeout). |
| `AuthenticationError` | `AUTHENTICATION` | The provider rejected the API key. |
| `InsufficientBalanceError` | `INSUFFICIENT_BALANCE` | Provider reported insufficient balance. |
| `UnsupportedChallengeError` | `UNSUPPORTED_CHALLENGE` | Kind unsupported by the provider. |
| `InvalidChallengeError` | `INVALID_CHALLENGE` | Challenge failed client-side validation. |
| `TaskTimeoutError` | `TASK_TIMEOUT` | The solve/wait budget was exhausted. |
| `RateLimitError` | `RATE_LIMIT` | Rate limiting exhausted the retry policy. |
| `ServiceBusyError` | `SERVICE_BUSY` | No workers free (provider capacity). |
| `NoSolutionError` | `NO_SOLUTION` | Workers could not solve the captcha. |
| `EmptySolutionError` | `EMPTY_SOLUTION` | "Solved" response with an empty payload. |
| `InvalidConfigError` | `INVALID_CONFIG` | An explicitly-invalid configuration value. |
| `ClientClosedError` | `CLIENT_CLOSED` | Operation on a closed client. |
| `ProviderError` | `PROVIDER` | Unclassified provider error (also malformed bodies). |

`EmptySolutionError` subclasses `ProviderError` but keeps its own kind.

## Handling errors

```python
from unicaptcha import ErrorKind, NoSolutionError, TaskTimeoutError

try:
    result = client.solve(challenge)
except NoSolutionError:
    print("workers could not solve it")
except TaskTimeoutError:
    print("budget exhausted")
except UnicaptchaError as exc:
    print(exc.kind, exc.raw_response[:80])
```

- Wrong-provider routing raises `TypeError` pre-flight (no network
  traffic) — there is no dedicated exception for it.
- Status queries (`wait_ref`, `get_task_status`) **answer rather than
  raise**: they return a `TaskStatusResult` with a `PENDING`/`READY`/
  `NO_SOLUTION`/`UNKNOWN` status.

## Raw provider bodies

`raw_response` preserves the exact bytes the provider returned, which is
invaluable for debugging:

```python
except ProviderError as exc:
    print(exc.raw_response)   # b'{"errorId":1,...}'
```

## Reference

- [ErrorKind + exceptions](../api/errors.md)