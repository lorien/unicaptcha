# ADR-0061: Facade constructor parity

**Status:** Accepted (amends ADR-0051's parity principle; complements ADR-0007; `api_key` union per ADR-0063; `referral` kwarg per ADR-0072)
**Date:** 2026-08-23

## Context

ADR-0051 settled per-call parameter parity (`time=`, `retry=`,
`on_event=`) but was silent on facade **constructors**. Meanwhile the
README promises that 2Captcha-protocol mirrors (RuCaptcha) work "by
overriding the 2Captcha adapter's base URL", and ADR-0007 says facades
create their adapter internally — so `base_url` must be a facade
constructor parameter for the promise to hold. No ADR said so, nor
which of the universal client's many constructor kwargs facades accept.

## Decision

A facade constructor accepts the **adapter set** plus **every client
kwarg** of `Solver` / `AsyncSolver` except `adapters`:

```python
TwoCaptchaClient(
    api_key: SecretStr | str,        # adapter credentials (positional-first); str wrapped (ADR-0063)
    base_url: str | None = None,    # overrides default_base_url (RuCaptcha mirrors)
    referral: bool | str = True,    # affiliate id: True=project's, False=off, str=own (ADR-0072)
    # client kwargs, identical names/defaults/validation as Solver:
    name=..., time=..., retry=..., http=..., http_client=...,
    on_event=..., abandoned_registry_limit=...,
)
```

- `base_url=None` resolves to the adapter's `default_base_url`
  (ADR-0053) — 2Captcha-protocol mirrors change one argument.
- All validation rules apply unchanged: config mutual exclusion
  (`http` vs `http_client`, ADR-0049), config construction checks
  (ADR-0042), event-handler attachment rules (ADR-0044).
- `adapters=` is absent by construction: the facade's provider is
  static (ADR-0007); passing one is not an option to forget.

## Rationale

- Parity as a tier rule, not a per-method accident: same knobs, same
  names, same semantics on both tiers — what ADR-0051 established for
  calls now holds for construction.
- The README's mirror-provider story becomes a documented signature,
  not folklore.
- Everything `Solver` accepts describes the engine/HTTP layer the
  facade also owns (peers) — refusing any of them would force the
  facade user into a universal client for no architectural reason.

## Alternatives considered

- **`adapter=` injection instead of `api_key`/`base_url`**: rejected;
  callers would construct adapters for the common case, adding a step
  and re-exposing the registry question the facade exists to hide.
  (An adapter-typed escape hatch can be added later if demanded.)
- **Facades take only `api_key`/`base_url`**: rejected; no path to
  shared `http_client` pools (ADR-0007's own sharing story) or any
  tuning.
- **`base_url` on `HttpClientConfig`**: rejected; it is provider
  identity, not transport tuning — wrong home, and mirrors the
  per-provider default table (README).
