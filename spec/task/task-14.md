# Task 14: Capsolver adapter + facade

Status: new

First read `var/analysis-py-capsolver-python.md`.

Implement `provider/capsolver/`:

- `challenge.py`: concrete challenge subclasses per ADR-0076 (GeeTest
  v3 only; Turnstile via `AntiCloudflareTask` with `metadata`; dict-style
  pass-through extras).
- `solution.py`: concrete solution subclasses.
- `adapter.py`: `CapsolverAdapter` — payload build + parse, instant-task
  fast path (`instant_answer`), referral embedding (ADR-0072), error
  mapping incl. HTTP-status keyed kinds.
- `client.py`: `CapsolverClient` / `AsyncCapsolverClient` facades.

References: ADR-0001, ADR-0007, ADR-0051, ADR-0061, ADR-0071, ADR-0072,
ADR-0075, ADR-0076.