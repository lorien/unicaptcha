# ADR-0052: Adapter naming — `adapters=` argument, `<Provider>Adapter` classes

**Status:** Accepted (amends ADR-0005, ADR-0036, ADR-0041, ADR-0042; corrects ADR-0014 example)
**Date:** 2026-08-23

## Context

The universal client's constructor argument was specified as
`providers=[...]`, but the objects it accepts are adapter instances — not
providers (the services) and not facades (peers, never registerable).
"Provider" already has a precise meaning in the taxonomy: the external
service, identified by its provider string (`Result.provider`,
`TaskRef.provider`, `SolveEvent.provider`, `get_balance(provider)`
discriminator). Overloading it with a second, object-shaped meaning made
the tier boundary fuzzy: the README example even showed a
`TwoCaptchaProvider` class that exists nowhere in the design.

During review, two further candidates were explored before settling:
qualifying the term (`ProviderAdapter`) and collapsing it back onto the
object itself (`Provider`). Both were rejected — see Alternatives —
leaving bare **Adapter** as the term.

## Decision

- Constructor kwarg: `adapters=[TwoCaptchaAdapter(...), MyServiceAdapter(...)]`
  on `CaptchaSolver` / `AsyncCaptchaSolver`.
- Class naming: shipped adapters are `<Provider>Adapter`
  (`TwoCaptchaAdapter`, `AntiCaptchaAdapter`, `CapMonsterAdapter`);
  third-party convention `<Name>Adapter` — parallel to `<Provider>Client`
  (ADR-0036) and `<Provider><Kind>Challenge`. The base contract class is
  `BaseAdapter`, symmetric with `BaseChallenge`.
- Terminology rule: **provider** is the identity concept only — the
  service and its provider string (ADR-0055: the adapter attribute is
  `provider`). **Adapter** is the object implementing
  the translation contract. The extension feature is the **adapter SDK**.
  Facades remain peers, never registerable.
- The adapter contract's enforcement mechanism is settled in ADR-0053:
  `BaseAdapter` is an ABC.

## Rationale

- Names that match the accepted type prevent exactly the confusion that
  produced this ADR: `providers=[facade]` looks plausible,
  `adapters=[facade]` looks wrong.
- With facade clients in every provider package, the suffix pair does the
  tier-disambiguation work: `<Provider>Adapter` (pure translation
  object) vs `<Provider>Client` (I/O facade) differ as obviously as
  names can manage, without a verbose compound.
- One word per concept, extending ADR-0036's rationale that names make
  the tier system self-evident in type errors and autocomplete.

## Alternatives considered

- **Keep `providers=`**: rejected; permanent terminological fuzziness
  between the service identity and the registered object.
- **Keep `providers=`, fix README class name only**: cosmetic; the
  overload survives in every signature and doc.
- **`Provider` objects + `providers=`** (revert to the original shape,
  made consistent): rejected; "provider" would again mean both the
  service and the in-code object, and every provider package would grow
  a near-namesake footgun pair — `TwoCaptchaProvider` (pure, takes
  `api_key=`) vs `TwoCaptchaClient` (I/O facade, takes `api_key=`) —
  differing by one suffix character.
- **`ProviderAdapter` family** (`TwoCaptchaProviderAdapter`,
  `BaseProviderAdapter`): briefly adopted this session, then reverted;
  the qualifier binds the term to the provider concept, but reads
  verbose while the Adapter/Client suffix pair already disambiguates
  the tiers.
- **`ServiceAdapter` family** (`TwoCaptchaServiceAdapter`): rejected;
  "service" is used descriptively (goals, README prose) but is not the
  formal identity word — adopting it here forks terminology unless the
  whole identity vocabulary (`provider`, `Result.provider`, ...) renames
  too, for no clarity gain.
