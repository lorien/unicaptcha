# ADR-0066: Challenge call-style — keyword-only fields, positional payload

**Status:** Accepted (amends ADR-0006)
**Date:** 2026-08-23

## Context

Challenge construction style was unspecified. Two hazards shaped the
owner's decision:

- `RecaptchaV2Challenge("6Le...", "https://site.com")` — two
  anonymous same-typed strings; swapping `sitekey`/`pageurl` or
  dropping one and shifting the rest is silent.
- Conversely, `ImageChallenge(body=...)` — needless ceremony for a
  kind whose single field is unambiguous.

Separately, the design audit flagged a frozen-dataclass wart:
provider subclasses adding non-default fields after kind-base fields
with defaults (`invisible=False`, `proxy=None`) hit class-creation
`TypeError` under classic ordering rules.

## Decision

- **Kind-base fields are keyword-only**, with one exception: a kind's
  single payload field is positional-or-keyword.
  - `ImageChallenge(Path("test.png"))` / `ImageChallenge(body=...)`
  - `TextChallenge("2+2?")` / `TextChallenge(text=...)`
- Multi-field kind bases require keywords for all fields:
  - `RecaptchaV2Challenge(sitekey="...", pageurl="...",
    invisible=False)` — `sitekey`/`pageurl` keyword-required;
    `invisible` keyword-only, default `False`
  - `RecaptchaV3Challenge(sitekey=..., pageurl=..., action=None,
    min_score=...)`, `HCaptchaChallenge(sitekey=..., pageurl=...)` —
    same
- **Provider extras** (`numeric=True`, `phrase=...`, `proxy=...`)
  inherit keyword-only — they are optional by nature.
- **Mechanism**: `dataclasses` `kw_only` (field-level or class-level)
  on non-payload fields. Python 3.10+; the project floor is 3.11
  (ADR-0004) — no cost.
- **Consequence recorded**: keyword-only fields carry no
  default-ordering constraints across inheritance, eliminating the
  non-default-after-default class-creation failure for provider
  subclasses — the audit wart dies by construction.

## Rationale

- Same-typed anonymous strings can no longer be swapped or shift when
  one is dropped; the error is immediate and names the missing field.
- Single-payload kinds keep the shortest honest call — no ceremony
  where no ambiguity exists.
- One uniform rule, two shapes; no per-class style decisions to
  remember.

## Alternatives considered

- **All positional-or-keyword** (default dataclass behavior): rejected;
  the swap hazard is real and silent.
- **Keyword-everything** (payload too): rejected; ceremony without
  ambiguity on single-field kinds.
- **Per-class ad-hoc choices**: rejected; unmemorable policy.
