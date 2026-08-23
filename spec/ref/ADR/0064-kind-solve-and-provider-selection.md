# ADR-0064: Kind-level solve with optional provider selection

**Status:** Accepted (amends ADR-0005, ADR-0045, ADR-0048; partially covers deferred item 4)
**Date:** 2026-08-23

## Context

ADR-0005 made the concrete challenge class the only provider-choice
vehicle: "There is deliberately no provider-agnostic solve on the
universal client." Owner review reopened this: the challenge is a
description of a solvable thing; making the *kind base* instantiable
and letting `solve()` route it is a legitimate universal-tier use,
especially for the common single-provider client. The objection that
killed the old "universal `solve_image(...)` methods" proposal —
union-polluted parameter surfaces — does not apply: the universal
surface here is *minimal* (universal fields only), honest by
construction.

The selection mechanism among multiple supporting providers was
settled by the owner: optional `provider: str | None`; when absent,
uniform random choice.

## Decision

### Instantiable kind bases

`ImageChallenge`, `TextChallenge`, `RecaptchaV2Challenge`,
`RecaptchaV3Challenge`, `HCaptchaChallenge` become **instantiable**,
carrying universal fields only. Provider extras still require the
concrete class. Solutions remain non-instantiable (deliberate
asymmetry: a bare challenge plus routing is a complete request; a
bare solution would be a fabrication — only adapters construct
solutions). Amends ADR-0048's "bases are abstract" rule; the abstract
rule survives for solutions (ADR-0035, ADR-0056).

### solve() signature

```python
solve(challenge, provider: str | None = None, solve=..., retry=..., on_event=...)
```

on `CaptchaSolver` / `AsyncCaptchaSolver` (facades unchanged,
ADR-0051/0061):

- **Kind-base challenge, `provider=None`**: uniform random choice
  among registered adapters whose `challenges` includes a subclass of
  that kind base. Stateless per call (no stickiness, no weighting);
  each solve independent. The chosen adapter is visible in
  `Result.provider` and the `submitted` event — no new
  observability surface. Billing caveat documented: any registered
  supporting account may be billed; pass `provider=` to control it.
- **Kind-base challenge, `provider="capmonster"`**: that adapter.
  Unknown provider string -> pre-flight `TypeError` (ADR-0045
  discriminator treatment). Registered adapter that does not support
  the kind -> pre-flight `UnsupportedCaptchaError` (ADR-0057
  client-side scope). No supporting adapter at all ->
  `UnsupportedCaptchaError`.
- **Concrete challenge, matching `provider=`**: allowed; redundant,
  ignored.
- **Concrete challenge, contradicting `provider=`**: pre-flight
  `TypeError` naming both parties ("challenge is
  CapMonsterImageChallenge, provider 'capmonster', but provider=
  'twocaptcha'").
- **Concrete challenge, no `provider=`**: unchanged behavior
  (ADR-0005 type-based dispatch).

### Engine upcast rule

The engine derives the provider's concrete class from the adapter's
`challenges` frozenset (the unique member subclassing the kind base)
and constructs it with the universal fields before `build_payload`.
Adapters never see kind-base instances; the adapter SDK contract is
untouched. Custom kinds (direct `BaseChallenge` subclasses with no
kind base) are unaffected — no kind dispatch exists for them, and
their bases stay abstract (nothing universal to instantiate).

### Typing

`solve(ImageChallenge(...))` returns `Result[ImageSolution]` via the
existing challenge->solution link (ADR-0048); the returned solution
is a provider subclass at runtime, the kind base statically — same
as today.

### Test determinism

The random-pick step is an injectable internal function (same
pattern as the clock/sleep seam, architecture.md §10): production
uses uniform random choice; tests inject a fixed picker for
deterministic assertions. Internal detail, not public API.

## Rationale

- Single-provider universal clients get the shortest honest code:
  `solver.solve(ImageChallenge(body=data))`.
- Random is honest zero-config: no false optimization claims (not
  cheapest, not fastest — just fair distribution over time), and the
  outcome is always visible in `Result.provider`.
- The engine upcast keeps adapters pure and the SDK stable; the
  registry already holds everything needed to derive the concrete
  class.

## Alternatives considered

- **Keep ADR-0005's concrete-class-only dispatch**: superseded by
  owner decision; the "no honest universal surface" argument does not
  apply to a minimal universal-field surface.
- **Implicit unique-adapter selection (no `provider=`, error when
  ambiguous)**: rejected by owner; random chosen instead.
- **Registration-order priority (first supporting adapter wins)**:
  rejected; silent choice, billing surprise, hidden semantics in
  list order.
- **Per-kind routing table config**: rejected; decision far from
  call site, config creep toward policy routing (still deferred,
  item 4).
- **Forbid `provider=` with concrete challenges entirely**: rejected;
  redundant agreement is harmless and occurs naturally in templated
  code; contradiction still errors.
