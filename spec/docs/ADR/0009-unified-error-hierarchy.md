# ADR-0009: Unified error hierarchy

**Status:** Accepted (amended: SolveCancelledError removed; UnknownTaskError removed; InvalidConfigError and ClientClosedError added; UnsupportedChallengeError scope widened by ADR-0057; ServiceBusyError added by ADR-0059 amendment; EmptySolutionError added by ADR-0040 amendment; renamed 2026-08-24: `UnsupportedCaptchaError` → `UnsupportedChallengeError`, `UnsolvableCaptchaError` → `NoSolutionError`, `SolveTimeoutError` → `TaskTimeoutError`, `ErrorKind.SOLVE_TIMEOUT` → `TASK_TIMEOUT`; ErrorKind values mirror class names — class minus `Error`, SCREAMING_SNAKE — per the 1:1 invariant)
**Date:** 2026-08-22, amendments 2026-08-23, 2026-08-24

## Context

Providers return heterogeneous error codes (2Captcha strings like
`ERROR_ZERO_BALANCE`, Anti-Captcha/CapMonster numeric codes). Callers must
catch failures without knowing provider dialects. Two contradictions with
other decisions were later found and fixed: a `SolveCancelledError` that
swallowed `CancelledError` (breaks asyncio protocol; removed by ADR-0016)
and an `UnknownTaskError` that conflicted with status-query semantics
(removed by ADR-0050).

## Decision

```
UnicaptchaError                    kind: ErrorKind; raw_response: bytes
+-- NetworkError
+-- AuthenticationError
+-- InsufficientBalanceError
+-- UnsupportedChallengeError        provider lacks the operation/kind (both sides, ADR-0057)
+-- InvalidChallengeError          client-side challenge validation
+-- TaskTimeoutError
+-- RateLimitError
+-- ServiceBusyError               provider capacity: no workers free (ADR-0059 amendment)
+-- NoSolutionError
+-- InvalidConfigError
+-- ClientClosedError
+-- ProviderError                  unclassified provider errors
    +-- EmptySolutionError          solved-but-empty payload (ADR-0040 amendment)
```

- Base carries `kind: ErrorKind` and `raw_response: bytes` (verbatim body).
  No `provider_code` attribute: adapters normalize semantics into the
  hierarchy; the original bytes are attached for debugging.
- `ErrorKind` (13 values): NETWORK, AUTHENTICATION, INSUFFICIENT_BALANCE, UNSUPPORTED_CHALLENGE,
  INVALID_CHALLENGE, TASK_TIMEOUT, RATE_LIMIT, SERVICE_BUSY, NO_SOLUTION,
  EMPTY_SOLUTION, CLIENT_CLOSED, INVALID_CONFIG, PROVIDER. First nested leaf:
  `EmptySolutionError` under `ProviderError` (ADR-0040 amendment).
- Message travels via standard `Exception` machinery.
- Every wrapped cause uses `raise ... from cause`; event-handler exceptions
  propagate raw (ADR-0018).
- `UnsupportedChallengeError` covers server-side task-type rejections
  (task type unavailable on plan/account, provider dropped support)
  **and** client-side pre-flight coverage gaps such as the report-bad
  support matrix (ADR-0057); wrong-provider arguments are `TypeError`
  (ADR-0045).
- Malformed provider responses (HTTP 200, unparseable/wrong-shape body)
  map to `ProviderError` with the parse failure as `__cause__`
  (ADR-0040).

## Rationale

- One exception family to catch; `kind` for programmatic handling; raw
  bytes for forensics. Normalization lives in adapters, mapped once.
- Removing `provider_code` (owner decision) avoids the string-vs-int code
  storage problem entirely; semantics live in the class/kind, evidence in
  `raw_response`.

## Alternatives considered

- **`provider_code: str | int`**: rejected by owner; mixed-type attribute
  is a design smell; superseded by kind + raw bytes.
- **Parsed-JSON `raw_response`**: rejected; owner required original bytes.
- **`SolveCancelledError`**: removed; violates asyncio cancellation
  contract (ADR-0016).
- **`UnknownTaskError`**: removed; "no such task" is a returned status on
  queries (ADR-0050).
- **Finer splits** (per-HTTP-status exceptions etc.): rejected; the 11-leaf
  set covers every real handling branch without noise.
