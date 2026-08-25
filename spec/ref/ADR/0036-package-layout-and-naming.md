# ADR-0036: Package layout and naming

**Status:** Accepted (amended: `unicaptcha.types` module added; adapter classes named `<Provider>Adapter` per ADR-0052; universal tier renamed `Solver`/`AsyncSolver` per ADR-0062, Client suffix scoped to facades; amended 2026-08-24: singular/plural naming rule — root files plural, root directories singular, provider internals singular one-per-concern; `challenge/` kind-base package added per ADR-0048)
**Date:** 2026-08-22, amendments 2026-08-23, 2026-08-24

## Context

The package structure must host two client tiers, provider packages,
public model vocabulary, and internals, with names that make the two-tier
API obvious.

## Decision

```
unicaptcha/
    __init__.py        # curated re-exports: clients, errors, ErrorKind,
                       # TaskResult, TaskStatusResult, TaskEvent, TaskRef, SecretStr,
                       # configs, Proxy/ProxyKind, kind bases
    _version.py        # single version source
    client.py          # Solver / AsyncSolver (ADR-0062)
    errors.py          # hierarchy + ErrorKind
    events.py          # TaskEvent
    types.py           # public model vocabulary; re-exported from root
    challenge/         # abstract challenge kind bases (ADR-0048)
    solution/          # abstract solution kind bases (ADR-0035)
    provider/          # one package per provider
        twocaptcha/    # challenge.py, solution.py, adapter.py, client.py
        anticaptcha/
        capmonster/
        capsolver/     # ADR-0071
    _internal/         # engine, http layer implementation, clock, scrubbing
```

- **Naming rule** (2026-08-24 amendment): root package **files** are
  plural (`types.py`, `errors.py`, `events.py`); root package
  **directories** are singular (`challenge/`, `solution/`, `provider/`,
  `_internal/`); everything inside a provider package is singular, one
  file per concern (`challenge.py`, `solution.py`, `adapter.py`,
  `client.py`).
- **`challenge/`** (2026-08-24 amendment): abstract challenge kind bases
  (ADR-0048) live in a root package symmetric with `solution/`, one file
  per kind (`base.py`, `image.py`, `text.py`, `recaptcha_v2.py`,
  `recaptcha_v3.py`, `hcaptcha.py`, `funcaptcha.py`, `geetest.py`,
  `turnstile.py`).

- **Class names**: `Solver` / `AsyncSolver`
  (ADR-0062, was `UnicaptchaClient` / `MultiClient` earlier);
  `TwoCaptchaClient` / `AsyncTwoCaptchaClient` etc. — every facade
  class ends in `Client` (owner refinement of the initial `Unicaptcha`
  proposal; suffix scoped to facades by ADR-0062).
- Challenges: `<Provider><Kind>Challenge`; solutions:
  `<Provider><Kind>Solution`.
- **`unicaptcha.types`**: public home for `Proxy`/`ProxyKind` and the model
  vocabulary; the root re-exports everything, so `from unicaptcha import
  Proxy` is canonical while code stays organized. A `unicaptcha.util`
  module was explicitly rejected (junk-drawer reputation; these are domain
  types, not utilities).
- Facade method names: `solve_image`, `solve_text`, `solve_recaptcha_v2`,
  `solve_recaptcha_v3`, `solve_hcaptcha`; aux ops identical on both tiers.
- Root `__init__` exports core vocabulary only; provider classes require
  `from unicaptcha.provider.<name> import ...` (four providers x nine
  kinds x two clients would drown the root).

## Rationale

- Client-suffixed names make the tier system self-evident in type errors
  and autocomplete.
- types-module + root re-exports balances organization against import
  friction.
- Flat provider subpackages mirror each other, simplifying the adapter
  SDK story.

## Alternatives considered

- **`Unicaptcha`/`AsyncUnicaptcha` naming**: rejected; inconsistent with
  facade naming.
- **`unicaptcha.util`**: rejected; naming invites accumulation of
  unrelated code.
- **Everything re-exported from root**: rejected; root namespace
  explosion.
