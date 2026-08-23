# ADR-0006: Provider-specific challenge classes

**Status:** Accepted (amended 2026-08-23: frozen dataclasses instead of pydantic; amended by ADR-0048 adding kind bases; call-style policy per ADR-0066)
**Date:** 2026-08-22

## Context

Challenges (task descriptions) must express exactly what each provider
supports. A shared "generic image challenge" would either union-pollute
parameters or silently drop provider-specific ones. Implementation substrate:
pydantic v2 models were initially chosen; later review dropped pydantic
entirely.

## Decision

- Challenge classes are **provider-specific and kind-specific**:
  `TwoCaptchaImageChallenge`, `AntiCaptchaRecaptchaV2Challenge`, ... Each
  provider package contains only the kinds that provider supports; fields
  match exactly what that provider accepts (CapMonster classes carry no
  proxy fields at all, for instance).
- Challenges are **frozen dataclasses** with `__post_init__` validation
  raising `InvalidChallengeError` directly, fail-fast at construction
  (ADR-0041 drops the original pydantic choice and its ValidationError
  bridging problem).
- Proxy-capable challenge kinds carry an optional `proxy: Proxy | None`
  field; the adapter selects the provider's with-proxy vs proxyless task
  type based on its presence (ADR-0012).
- Universal per-kind fields live on public kind bases
  (`RecaptchaV2Challenge` etc.), with provider subclasses adding only their
  extras (ADR-0048).

## Rationale

- Fail-fast validation: caller mistakes surface at the construction line,
  before any network call, in the library's own exception hierarchy.
- Frozen dataclasses keep the dependency count at one (httpx); validation
  for parameter-bag models is a handful of explicit checks; a ~30-line
  SecretStr replaces pydantic's (ADR-0014).
- Provider-specific classes are the mechanism that makes type-based
  dispatch (ADR-0005) honest.

## Alternatives considered

- **pydantic v2 frozen models** with a wrapper re-raising
  `InvalidChallengeError` around `ValidationError`: initially accepted,
  later rejected; heavy dependency (compiled core) for simple parameter
  bags, and two exception families for one failure kind.
- **attrs**: rejected; same hand-rolled cost as dataclasses without stdlib
  status.
- **Validate only at solve time**: rejected; errors surface far from cause.
- **Generic per-kind classes with provider argument**: rejected; loses
  per-provider field fidelity.
