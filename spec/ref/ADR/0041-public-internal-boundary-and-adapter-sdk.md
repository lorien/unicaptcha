# ADR-0041: Public/internal boundary and the adapter SDK

**Status:** Accepted (amended: pydantic dropped — frozen dataclasses; adapter SDK public from day one)
**Date:** 2026-08-23

## Context

Two interlocking decisions: (1) which import surface is public vs
internal, given ~15 internal modules that will refactor heavily; (2)
whether third parties can write provider adapters. An early lean said
"built-in adapters only for v1"; the owner overruled: public adapter SDK
from day one.

## Decision

**Public surface** (documented, root + provider packages):

- Root `unicaptcha`: clients, errors + ErrorKind, Result/TaskStatus/
  SolveEvent/TaskRef, SecretStr, configs, Proxy/ProxyKind, challenge and
  solution kind bases.
- `unicaptcha.providers.<name>`: that provider's challenges, solutions,
  adapter class, facades.
- **The adapter SDK contract**: adapter base machinery is public API.
  Custom adapters implement the contract (kind, challenges frozenset,
  pure translation methods, error mapping, optional per-kind defaults)
  and register via `UnicaptchaClient(providers=[...])`.
- The injectable HTTP layer is exposed as a public **Protocol**
  (what may be injected); its implementation stays `_internal`.

**Internal** (`unicaptcha._internal/`, underscore modules, no stability
promise): SolveEngine, HTTP layer implementation, clock/sleep seam,
scrubbing, adapter base machinery internals. CI enforces isolation: public
modules never import another provider's package; the reference third-party
adapter (ADR-0046) never imports `_internal`.

**Models are frozen dataclasses** (supersedes pydantic): `__post_init__`
validation raises `InvalidChallengeError`/`InvalidConfigError` directly —
one exception family for caller mistakes; hand-rolled `SecretStr`;
runtime dependencies reduced to httpx alone.

**Experimental caveat**: the project declares no stability obligations
even for the public surface (goals.md). The boundary communicates intent
and gets us honest bug reports ("you broke documented API" vs "internal
import stopped working"), not commitment.

## Rationale

- Declaring internals public would freeze, from day one, the least stable
  surface — a tax on exactly the refactoring early development needs.
- The owner wants extensibility now; the layered architecture (pure
  adapters + engine) makes the SDK contract natural rather than bolted
  on.
- pydantic removal: parameter-bag models don't earn a compiled-core
  dependency; dataclasses + explicit validation keep one dependency and
  one exception family.

## Alternatives considered

- **Built-in adapters only** (adapters `_internal`): rejected by owner.
- **Everything public**: rejected; freezes accident-prone internals.
- **pydantic models with error bridging**: superseded; heavy dependency,
  two exception families for one failure kind.
- **De facto extensibility (subclassable but undocumented)**: rejected;
  the SDK is a product feature, not an accident.
