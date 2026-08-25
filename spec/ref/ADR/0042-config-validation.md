# ADR-0042: Config validation — InvalidConfigError, fail-fast at construction

**Status:** Accepted (amended by ADR-0052: the argument is the adapters list; amended 2026-08-24: added the `backoff_cap >= backoff_base` invariant)
**Date:** 2026-08-23, amendment 2026-08-24

## Context

Config values can be nonsense (`total_timeout=0`, `poll_interval=-5`,
`max_attempts=-1`, `adapters=[]`). When are they checked and as what
error? Challenges already fail fast with `InvalidChallengeError`; config
mistakes are the same class of caller bug.

## Decision

- **Fail at config construction**: frozen dataclass `__post_init__`
  validates explicit values and raises **`InvalidConfigError`**
  (`ErrorKind.INVALID_CONFIG`), a leaf under `UnicaptchaError`.
- `None` is always valid (it means "unspecified", ADR-0043); only explicit
  bad values raise.
- Per-type invariants: `total_timeout > 0`, `poll_interval > 0`,
  `max_attempts > 0`, `backoff_base > 0`, `backoff_cap > 0`, and
  **`backoff_cap >= backoff_base`** (a cap below its own base is a
  backoff that cannot back off) — all `InvalidConfigError`.
- Constructed config objects are trustable: per-call overrides can never
  smuggle garbage past construction.
- Client construction additionally validates composite invariants:
  empty/None adapters list, duplicate kinds (ADR-0037, `ValueError`),
  non-adapter objects in `adapters` (`TypeError`, ADR-0053),
  `http` config + injected httpx client together (ADR-0049).

## Rationale

- The mistake is caught on the line that made it, not three layers later
  mid-solve.
- A typed leaf in the one exception family beats bare `ValueError` for
  catchability, consistent with the challenges precedent.

## Alternatives considered

- **Validate at client construction**: rejected; traceback points at the
  passing site, not the construction site.
- **Validate lazily at first use**: rejected; worst debuggability,
  repeated work per call.
- **Plain `ValueError` from dataclasses**: rejected; outside the
  hierarchy.
