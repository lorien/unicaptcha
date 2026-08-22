# ADR-0035: Solution bases non-instantiable

**Status:** Accepted
**Date:** 2026-08-23

## Context

Solution kind bases (`ImageSolution`, `RecaptchaV2Solution`, ...) are typing
constructs: the static return type of the universal path and the
isinstance/generic-programming vocabulary. No adapter ever constructs a
bare base — always the provider subclass. Should users be able to?

## Decision

- Bases **reject direct instantiation**: `__post_init__` raises `TypeError`
  when `type(self) is Base`. They are abstract types by contract and by
  runtime enforcement.
- Adapters always construct provider subclasses (e.g.,
  `AntiCaptchaRecaptchaV2Solution`).
- Facade methods return the narrower static type
  (`Result[TwoCaptchaImageSolution]`); challenges link to their solution
  type so even the universal `solve()` can be statically precise while
  remaining generic.

## Rationale

- A user-constructed bare `ImageSolution` would be an object no code path
  produces — harmless but misleading; cheap to forbid with frozen
  dataclasses.
- Enforcement documents the taxonomy: bases are contracts, subclasses are
  reality.

## Alternatives considered

- **Permissive concrete bases**: rejected; accidental bare construction
  invites type-confusion bugs (e.g., isinstance passing for the wrong
  reason).
