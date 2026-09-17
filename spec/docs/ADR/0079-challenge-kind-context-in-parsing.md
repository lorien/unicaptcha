# ADR-0079: Challenge-kind context in response parsing

**Status:** Accepted (amends ADR-0041/0053: adapter parse methods gain an
optional `challenge_type`; amends ADR-0067/0058: `TaskTicket` carries it
into status parsing)
**Date:** 2026-09-17

## Context

Adapters parsed solutions from the response **shape** alone
(ADR-0058/0075: `parse_task_status(raw)` → `_solution_from(solution)`).
Where every kind has a distinct wire shape this is unambiguous, but
2Captcha/RuCaptcha document a **byte-identical** solution for reCAPTCHA
v2 and v3:

```json
{"gRecaptchaResponse": "…", "token": "…"}
```

The library's task-11 future-task note had already named the remedy:
thread challenge-kind context into status parsing (engine change) rather
than guessing from keys. Live reproduction confirmed the failure: a v2
invisible task on `api.rucaptcha.com` returned that exact shape and was
typed as `TwoCaptchaRecaptchaV3Solution`. The same latent collision
exists on the other three providers whenever a v3 answer omits `score`
(they detect v3 by the `score` key alone).

## Decision

- The engine passes the submitted challenge's **concrete class** into
  the adapter parsing methods:
  `parse_submit_response(raw, *, challenge_type=None)` and
  `parse_task_status(raw, *, challenge_type=None)`. The compat base
  forwards it to `_solution_from(solution, *, challenge_type=None)`.
  The keyword defaults to `None`.
- Adapters treat the challenge kind as authoritative for colliding
  shapes (reCAPTCHA v2 vs v3 on all four providers). Shape dispatch
  remains the fallback and still resolves the unambiguous kinds
  (image/text/GeeTest/token-only).
- `TaskTicket` gains `challenge_type`, so the two-phase
  `submit()` → `wait()` path has the same context as `solve()`. The
  ticket carries the **class**, never the challenge instance, so proxy
  credentials cannot leak through ticket reprs or pickles.
- `wait_ref()` and `get_task_status()` address a bare `TaskRef` and have
  no kind to offer; their solutions remain shape-dispatched. This is the
  known boundary of the mechanism, and the reason the fallback stays.

## Rationale

- When wire shapes collide, the request context is the only correct
  discriminator. Passing it into the response parser is standard
  protocol-client design and keeps adapters pure translators (ADR-0041).
- Optional keyword-only parameter: direct calls keep the old positional
  form. Adapters the engine drives add one keyword to each parse method
  (pre-1.0, no public stability obligations; ADR-0041's experimental
  caveat).
- Carrying the class rather than the instance keeps the public, frozen,
  picklable `TaskTicket` free of worker-context fields (proxies, cookies).

## Alternatives considered

- **Guess harder from response keys**: impossible; the documented v2 and
  v3 shapes are identical.
- **Keep shape dispatch and document the mislabel**: rejected; the kind
  is the caller's own request and must be honored.
- **Stateful adapter (remember the kind per task id)**: rejected; racy
  under concurrency and breaks the pure-translator contract.
- **Post-hoc re-typing at result construction**: rejected as the primary
  mechanism; it would leave `SubmitAccepted.instant_answer` shape-typed
  and give adapters the constructed object instead of the raw solution
  dict.
