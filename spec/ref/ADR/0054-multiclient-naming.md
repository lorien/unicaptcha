# ADR-0054: Universal client naming — `MultiClient` / `AsyncMultiClient`

**Status:** Accepted (amends ADR-0036 and every document naming the universal client class)
**Date:** 2026-08-23

## Context

The universal client was named `UnicaptchaClient` / `AsyncUnicaptchaClient`
(refinement of the original `Unicaptcha`/`AsyncUnicaptcha` proposal,
ADR-0036). Both forms share one defect: the naming grammar is
`<Provider>Client` for facades, and they fill the provider slot with the
library's own name. `UnicaptchaClient` therefore reads as a facade for a
"Unicaptcha" service — a fourth anti-captcha vendor that does not exist.
`Unicaptcha` additionally stutters (`unicaptcha.Unicaptcha`).

A long naming session swept role words, trait words, uniter words,
mechanism words, and hierarchy words. Everything claiming a mechanism or
position the architecture does not have died on contact with the design
facts; the survivors were `Client`, `MultiClient`, and `UniversalClient`.

## Decision

- The universal client classes are **`MultiClient`** and
  **`AsyncMultiClient`**.
- The provider slot stays empty: no library name in the `<Provider>Client`
  grammar; the multi-provider trait — the tier's defining difference from
  facades — is visible in the name.
- The `Client` suffix rule (ADR-0036) now applies to both tiers: universal
  `MultiClient`, facades `<Provider>Client`.
- The `adapters=` registration kwarg is unaffected (ADR-0052).
- Prose continues to say "universal client" as the descriptive tier term;
  only class names change.

## Rationale

- `MultiClient` next to `TwoCaptchaClient` teaches the tier system at a
  glance: multi-provider entry point vs single-provider facade.
- Describes the role (client) plus the one distinguishing trait
  (multi-provider) without coined words or project jargon.
- Survives every filter the session produced: no stutter, no fake vendor,
  no mechanism falsehood, no ecosystem collision.

## Alternatives considered

- **`Unicaptcha` / `AsyncUnicaptcha`**: rejected (ADR-0036); stutter,
  inconsistent with facade suffixing.
- **`UnicaptchaClient` / `AsyncUnicaptchaClient`**: superseded by this
  ADR; fills the provider slot with the library's own name — reads as a
  facade for a nonexistent "Unicaptcha" service.
- **`Client` / `AsyncClient`**: httpx symmetry and the cleanest call
  site, but a bare name that teaches nothing and collides with users'
  own `Client` classes; lost to the trait being visible.
- **`UniversalClient`**: the spec's own vocabulary made API; 14 chars of
  project jargon for external readers.
- **`Hub`**: coined uniter word; rejected by owner.
- **`Solver`**: names the job; `solver.solve(...)` stutters and collides
  with provider terminology.
- **`Session`**: lifecycle flavor; reads as HTTP session, invites
  confusion with httpx semantics.
- **`Gate` / `Broker` / `Router`**: middleware falsehood — imply an
  intermediary position on the data path; the library drives providers
  directly.
- **`Master`**: presupposes a subordinate tier — contradicts the peers
  decision (ADR-0007); word being retired ecosystem-wide.
- **`Worker`**: misattributes the labor (providers do the solving);
  background-queue connotation.
- **`Composer`**: names the superseded composition mechanism (ADR-0007);
  nothing is composed from multiple providers at runtime; PHP package
  manager collision.
- **`Dispatcher`**: dispatch is one line of `solve()`; the word implies
  forward-and-forget, not outcome ownership; strains the aux/lifecycle
  half of the surface.
