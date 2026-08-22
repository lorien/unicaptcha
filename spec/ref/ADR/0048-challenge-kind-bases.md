# ADR-0048: Challenge kind bases

**Status:** Accepted
**Date:** 2026-08-23

## Context

Solutions got a two-level taxonomy (abstract kind bases + provider
subclasses, ADR-0035); challenges had only concrete provider classes.
Three settled mechanisms need generic kind identity on challenges: the
engine's per-kind default table, the challenge->solution typing link, and
user-side isinstance/generic code.

## Decision

- Public abstract **kind bases**, symmetric with solutions:

```
BaseChallenge (public abstract root, open for custom kinds)
+-- ImageChallenge          body: bytes
+-- TextChallenge           text: str
+-- RecaptchaV2Challenge    sitekey: str; pageurl: str; invisible: bool
+-- RecaptchaV3Challenge    sitekey: str; pageurl: str; action; min_score
+-- HCaptchaChallenge       sitekey: str; pageurl: str
```

- **Universal fields live once** on the kind base; provider subclasses
  (`TwoCaptchaRecaptchaV2Challenge`, ...) add only provider-specific
  extras. Kills 15-fold duplication of `sitekey`/`pageurl` validation
  and documents the universal field set structurally.
- Bases are abstract (same non-instantiable enforcement as solutions).
- The challenge->solution type link is declared on kind bases (overridable
  per provider subclass where solution types narrow).
- **Dispatch stays concrete-class-keyed**: the adapter `challenges`
  frozenset lists concrete classes; inheritance serves field sharing,
  isinstance taxonomy, and kind derivation (MRO inspection), not
  dispatch.
- **Open root for custom kinds**: third-party adapters subclass
  `BaseChallenge` directly for kinds we never modeled (e.g. GeeTest);
  per-kind timing defaults come from the adapter's declaration with
  generic fallback (ADR-0041, ADR-0030).

## Rationale

- Symmetry with the solution taxonomy: one mental model across the
  model vocabulary.
- Centralized universal fields make "what every provider gets" precise
  and reviewable, mirroring the solution-base guarantee.
- Kind-as-metadata (enum ClassVar only) was rejected: flat, no field
  sharing, no isinstance taxonomy, universal fields exist only in docs.

## Alternatives considered

- **`kind: ClassVar[ChallengeKind]` metadata, no bases**: rejected for
  the duplication and lost taxonomy.
- **Dispatch on kind bases**: rejected; constructing the challenge is
  the provider choice (ADR-0005); base-keyed dispatch would blur it.
