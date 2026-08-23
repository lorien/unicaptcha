# ADR-0069: Worker context parameters — `user_agent`, `cookies`

**Status:** Accepted (amends ADR-0012; feeds deferred item 2)
**Date:** 2026-08-23

## Context

Competitive analysis (unicaps/anycaptcha) showed both libraries pass
`user_agent` and `cookies` per solve call. The concept is real but
their placement doesn't fit us — and it collides with vocabulary we
already have. Two different User-Agents exist:

| | Transport UA (have it) | Worker UA (the gap) |
|---|---|---|
| Who sends it | our HTTP layer, on API requests | the provider's solver loads the target page with it |
| Value | `unicaptcha/<version>` (ADR-0026) | the caller's browser-session UA |
| Why it matters | identification | token validity — tokens can be UA-bound; a mismatched worker UA may produce tokens the site rejects |

`cookies` is the same family: cookies handed to the solver for page
context (mandatory for future TikTok-style kinds; some providers also
report the worker's UA back on solutions — Anti-Captcha's
`user_agent` solution field).

## Decision

- **Worker context** = parameters the provider's solver uses when
  loading the target page. Two fields, both optional keyword-only
  challenge fields (`None` default = don't send), following the proxy
  precedent (ADR-0012): task data lives on the challenge, not per-call
  kwargs.

```python
RecaptchaV2Challenge(
    sitekey="...", pageurl="...",
    proxy=Proxy(...),
    user_agent="Mozilla/5.0 ...",
    cookies={"session": "abc"},
)
```

- **Types**: `user_agent: str | None`; `cookies: Mapping[str, str] |
  None` (hashability of frozen dataclasses knowingly traded for
  ergonomics; challenges are not hashed).
- **Per-provider surface** (universal field vs provider extra, per
  kind) folds into deferred item 2's per-provider field lists.
  Preliminary expectation: `user_agent` universal (all three
  providers accept `userAgent` on proxied tasks), `cookies`
  provider-specific; verify against each API reference at
  implementation.
- **Naming**: keep `user_agent` on the challenge — provider
  vocabulary (every API field is `userAgent`) and what users of other
  solver libraries already know. The constructor's transport
  `user_agent` (ADR-0024) is unchanged. The collision is defused by
  **no client-level default** for the worker field: the proxy
  precedent's client default is deliberately not mirrored, so the two
  meanings never share a constructor.

## Rationale

- Challenge placement keeps solve-method signatures provider-agnostic
  and the challenge the single source of task data — the same
  argument that settled proxies (ADR-0012).
- Vocabulary reservation now: future kinds (TikTok, FunCaptcha with
  blobs) require worker context; landing the placement rule before
  those kinds arrive avoids redesign.

## Alternatives considered

- **Per-call kwargs on solve methods** (their model): rejected;
  ADR-0012's precedent — kwargs duplicate per kind and leak task data
  out of the challenge.
- **`worker_user_agent` field name**: rejected; invents vocabulary no
  provider API uses.
- **Rename the transport kwarg** (`http_user_agent=`): rejected;
  churn in settled ADRs (ADR-0024) for a rarely used knob.
- **Client-level default for the worker UA**: rejected; would place
  both User-Agent meanings on one constructor and force a rename.
