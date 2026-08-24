# ADR-0048: Challenge kind bases

**Status:** Accepted (amended by ADR-0064: kind bases are instantiable, carrying universal fields, for kind-level solve; the abstract rule survives for solutions and custom-kind roots; amended 2026-08-24: kind bases live in the root `challenge/` package per the ADR-0036 naming rule)
**Date:** 2026-08-23, amendment 2026-08-24

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
- Bases are instantiable (amended by ADR-0064): a kind-base instance
  plus routing (`provider=` or random selection) is a complete
  universal-fields-only request. Solutions keep the
  non-instantiable rule (ADR-0035, ADR-0056).
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
- **Location** (2026-08-24 amendment): the kind bases live in the root
  `unicaptcha/challenge/` package, symmetric with `solution/`, one file
  per kind (`base.py`, `image.py`, `text.py`, `recaptcha_v2.py`,
  `recaptcha_v3.py`, `hcaptcha.py`, `funcaptcha.py`, `geetest.py`,
  `turnstile.py`); the root re-exports them (ADR-0036).

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
