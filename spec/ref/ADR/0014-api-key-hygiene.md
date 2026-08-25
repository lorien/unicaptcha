# ADR-0014: API key hygiene

**Status:** Accepted (amended: no env-var helpers; own SecretStr after pydantic was dropped; `SecretStr | str` accepted and normalized at construction per ADR-0063)
**Date:** 2026-08-22

## Context

API keys are secrets. They must never leak through `repr()`, logs,
exception messages, or the event stream. pydantic was initially to provide
`SecretStr`; its removal (ADR-0041) required a hand-rolled equivalent.

## Decision

- **Key delivery**: constructor argument only
  (`TwoCaptchaAdapter(api_key=...)`), typed `SecretStr | str` — a
  plain string is wrapped into `SecretStr` at construction
  (ADR-0063). No `from_env()` helpers (owner
  decision); environment handling belongs to the caller.
- **Storage**: hand-rolled `SecretStr` wrapper (~30 lines, public type)
  masking in `repr`/`str`.
- **No-leak guarantees**, documented as contracts:
  - `repr`/`str` of clients, adapters, challenges render keys as `***`
    (full mask, no partial characters — keys are short enough that
    fragments aid guessing);
  - log messages never contain key values at any level; scrubbing is
    targeted (we construct all payloads; keys occupy known positions);
  - `raw_response` on exceptions is scrubbed defensively before attach;
  - `TaskEvent` contains no credentials by construction.
- **Multiple keys / rotation**: out of scope for v1 (deferred.md item 6);
  one key per adapter instance; multi-account = multiple clients sharing
  an HTTP layer.

## Rationale

- Constructor-only keeps a single canonical path; env sugar multiplies
  conventions without adding capability.
- Own SecretStr keeps the dependency count at one while preserving the
  masking contract.

## Alternatives considered

- **`from_env()` classmethods** (`TWO_CAPTCHA_API_KEY` etc.): rejected by
  owner.
- **pydantic SecretStr**: superseded with pydantic's removal.
- **Key rotation support**: deferred; additive later via provider wrapper.
