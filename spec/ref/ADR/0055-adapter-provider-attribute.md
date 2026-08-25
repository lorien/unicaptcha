# ADR-0055: Adapter identity attribute — `provider`, not `kind`

**Status:** Accepted (amends ADR-0037, ADR-0041, ADR-0052, ADR-0053, ADR-0005's registry description in architecture.md)
**Date:** 2026-08-23

## Context

The adapter contract declared its identity as `kind: ClassVar[str]`
(e.g. `"twocaptcha"`). The word has ecosystem precedent as a category
discriminator (Kubernetes `kind: Pod`, Rust `io::ErrorKind`) — but those
name the *sort of thing*, never *which one*. Here the string names a
specific provider identity.

Worse, it was the third meaning of "kind" in one library: CAPTCHA kind
bases (`ImageChallenge` ... are "kinds", `<Provider><Kind>Challenge`)
and `ErrorKind` already own the word. ADR-0037 had to write "provider
kind 'twocaptcha'" just to disambiguate.

The spec already names the concept everywhere else: `TaskResult.provider`,
`TaskRef.provider`, `TaskEvent.provider`, `get_balance(provider)`.

## Decision

- The adapter identity attribute is **`provider: ClassVar[str]`** on
  `BaseAdapter` and every shipped/third-party adapter.
- The universal client's registry is keyed by `adapter.provider`;
  duplicates rejected with `ValueError` ("provider 'twocaptcha'
  registered twice", ADR-0037).
- Terminology: **"kind" now means only CAPTCHA kinds** (kind bases,
  `<Provider><Kind>Challenge`) **and `ErrorKind`**. The provider
  identity is always "provider". Prose like "kind string" becomes
  "provider string".

## Rationale

- One word per concept, end to end:
  `adapter.provider == TaskResult.provider == TaskRef.provider ==
  TaskEvent.provider == "twocaptcha"`.
- Ends the triple collision inside the vocabulary; ADR-0037's
  "provider kind" contortion disappears.
- The attribute returns a `str` while no `Provider` class exists
  (provider is a concept, deliberately never instantiated — naming
  session 2026-08-23); `.provider` as a string attribute is idiomatic
  (cf. `.region`, `.locale`).

## Alternatives considered

- **Keep `kind`**: precedent is for sort-of-thing, not which-one;
  triple collision stands.
- **`provider_id`**: "id" implies instance uniqueness; the value is a
  category shared by every adapter instance of that provider (two
  `TwoCaptchaAdapter`s in two clients share it — that is why ADR-0037
  forbids duplicates). Would also fork vocabulary against
  `task_id`, a genuine id.
- **`provider_key`**: reads as a credential next to `api_key`
  (SecretStr, ADR-0014) — unacceptable in a library whose documented
  contract is key hygiene; also names the dict-key mechanism, one use
  of the string, not the concept.
- **`provider_name`**: connotes display/human name.
- **`provider_kind`**: unambiguous but heavy; keeps "kind" alive for
  the identity concept it should release.
