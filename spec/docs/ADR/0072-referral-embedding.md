# ADR-0072: Referral embedding — affiliate ID by default, disable or replace per adapter

**Status:** Accepted (amends ADR-0053, ADR-0061; confirmed as-is 2026-08-24: referral embedding reviewed and locked)
**Date:** 2026-08-23, confirmation 2026-08-24

## Context

Libraries in this niche traditionally embed a referral ID
(`soft_id`/`softId`) in every payload — the provider pays the project
a commission per solve, credited to the software's author
(unicaps: 2Captcha `soft_id=2738`, Anti-Captcha `softId=940`, ...;
anycaptcha likewise). Our design embedded nothing, by omission rather
than decision. Owner decision: monetize by default, honestly — with
disable **and** replace (callers with their own software registration
credit themselves).

## Decision

- **Shipped adapters embed the project's affiliate ID by default** in
  every payload (2Captcha-family `soft_id`, Anti-Captcha `softId`,
  CapMonster/Capsolver equivalents).
- **Trinary kwarg on the adapter constructor**:

```python
TwoCaptchaAdapter("...")                     # referral=True: project's id
TwoCaptchaAdapter("...", referral=False)     # no id at all
TwoCaptchaAdapter("...", referral="4704")    # caller's own id
```

  `referral: bool | str = True` — stored by `BaseAdapter.__init__`
  (ADR-0053 member-table amendment); each shipped adapter serializes
  its provider's affiliate field per the value. Facades inherit the
  kwarg via constructor parity (ADR-0061):
  `TwoCaptchaClient("...", referral=...)`.
- **Third-party adapters: no default money flow.** The base stores
  the flag, embeds nothing; SDK authors opt in explicitly — the
  project's ids are never injected into someone else's service.
- **Actual project ids**: registered in each provider's software
  catalog at implementation time; recorded in code, never in docs or
  repository URLs.
- **Transparency**: README gains a short Funding note — what is
  embedded, why, how to disable or substitute one's own id.

## Rationale

- Revenue funds maintenance without changing user pricing —
  commission is provider-side; solvers cost the same either way.
- The trinary covers all real users: default (ours), privacy/cost
  purists (off), power users with their own registrations (theirs).
- Honest-by-documentation: the README note and the constructor kwarg
  make the flow discoverable, not hidden telemetry.

## Alternatives considered

- **No referral embedding**: rejected by owner; the norm in this
  niche is to monetize, and the honesty cost is paid down by the
  README note and the visible kwarg.
- **Silent embedding (no kwarg)**: rejected; hidden money flow in a
  library whose pitch is operational honesty.
- **Bool-only opt-out**: superseded by the owner's trinary — callers
  with their own software registration would have been forced to
  choose between crediting us and crediting nobody.
- **`soft_id`/`affiliate` kwarg naming**: rejected; provider-spelled
  field names differ (`soft_id` vs `softId`), `referral` is neutral
  and says the money thing honestly.
