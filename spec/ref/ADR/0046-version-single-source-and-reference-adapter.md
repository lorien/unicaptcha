# ADR-0046: Version single source and the reference adapter

**Status:** Accepted
**Date:** 2026-08-23

## Context

Two related closures: (1) how users read the version — a `__version__`
attribute duplicates pyproject's version unless single-sourced;
(2) the adapter SDK is public (ADR-0041), so the contract must stay
usable by external authors — internal refactors could silently break it.

## Decision

**Version single-sourcing.**

- `unicaptcha/_version.py` holds `__version__ = "0.1.0"`.
- pyproject reads the version from it (hatch version path) — one bump
  location.
- `unicaptcha.__version__` is importable without `importlib.metadata`
  (which breaks in source checkouts).
- CI release consistency checks (ADR-0021, ADR-0022) extended to
  tag == version == CHANGELOG section.

**Reference third-party adapter.**

- The test suite contains a minimal fake "myservice" provider that
  implements the documented adapter SDK contract **exactly as an
  external author would**: public imports only, no `_internal` access.
- It registers into a real `CaptchaSolver` and solves scripted
  challenges through the full engine in tests.
- CI asserts it never imports `_internal` — if an internal refactor
  breaks external adapter authors, CI fails instead of a user.
- Doubles as living documentation for the "authoring a custom provider"
  section.

## Rationale

- Single source eliminates drift by construction; the attribute serves
  the conventional read path.
- The reference adapter converts the SDK contract from documentation
  into an executable test; maintenance cost (updating it when the
  contract legitimately evolves) is precisely the signal we want.

## Alternatives considered

- **`importlib.metadata.version("unicaptcha")` only**: rejected; fails
  outside installed distributions, clunkier.
- **Version duplicated in pyproject + module**: rejected; drift risk
  relies on discipline where construction can guarantee it.
- **No contract test**: rejected; public SDK with no external-usage test
  is a promise without verification.
