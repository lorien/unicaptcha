# ADR-0052: Adapter naming — `adapters=` argument, `<Provider>Adapter` classes

**Status:** Accepted (amends ADR-0005, ADR-0036, ADR-0041, ADR-0042; corrects ADR-0014 example)
**Date:** 2026-08-23

## Context

The universal client's constructor argument was specified as
`providers=[...]`, but the objects it accepts are adapter instances — not
providers (the services) and not facades (peers, never registerable).
"Provider" already has a precise meaning in the taxonomy: the external
service, identified by its `kind` string (`Result.provider`,
`TaskRef.provider`, `SolveEvent.provider`, `get_balance(provider)`
discriminator). Overloading it with a second, object-shaped meaning made
the tier boundary fuzzy: the README example even showed a
`TwoCaptchaProvider` class that exists nowhere in the design.

## Decision

- Constructor kwarg: `adapters=[TwoCaptchaAdapter(...), MyServiceAdapter(...)]`
  on `UnicaptchaClient` / `AsyncUnicaptchaClient`.
- Class naming: shipped adapters are `<Provider>Adapter`
  (`TwoCaptchaAdapter`, `AntiCaptchaAdapter`, `CapMonsterAdapter`);
  third-party convention `<Name>Adapter` — parallel to `<Provider>Client`
  (ADR-0036) and `<Provider><Kind>Challenge`.
- Terminology rule: **provider** is the identity concept only — the
  service and its `kind` string. **Adapter** is the object implementing
  the translation contract. Facades remain peers, never registerable.
- This ADR does not settle the adapter contract's enforcement mechanism
  (structural Protocol vs ABC); that decision is pending separately.

## Rationale

- Names that match the accepted type prevent exactly the confusion that
  produced this ADR: `providers=[facade]` looks plausible,
  `adapters=[facade]` looks wrong.
- One word per concept, extending ADR-0036's rationale that names make
  the tier system self-evident in type errors and autocomplete.

## Alternatives considered

- **Keep `providers=`**: rejected; permanent terminological fuzziness
  between the service identity and the registered object.
- **Keep `providers=`, fix README class name only**: cosmetic; the
  overload survives in every signature and doc.
