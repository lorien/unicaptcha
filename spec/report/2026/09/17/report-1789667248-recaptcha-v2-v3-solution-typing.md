## Report on task: reCAPTCHA v2 solve returns a v3 solution object

### Task (ad-hoc, user-reported)

`TwoCaptchaClient.solve_recaptcha_v2(...)` on the RuCaptcha mirror
(`base_url="https://api.rucaptcha.com"`) returned
`TwoCaptchaRecaptchaV3Solution` instead of
`TwoCaptchaRecaptchaV2Solution`. The solve itself succeeded (a ~2.3k-char
token was billed and returned). Reproduction sitekey: the live Semrush
login page (`https://www.semrush.com/login/`), v2 invisible.

### Investigation

- Reproduced first against the live API with the current checkout (one
  real solve, `invisible=True`): the typed result was
  `TwoCaptchaRecaptchaV3Solution`.
- Captured the raw answer:
  `{"errorId":0,"status":"ready","solution":{"cookies":…,
  "gRecaptchaResponse":"…","token":"…"}}`. The `token` co-presence sent
  `_solution_from` down its "live-verified v3 shape" branch.
- Fetched the primary sources: 2Captcha's reCAPTCHA
  [v2](https://2captcha.com/api-docs/recaptcha-v2) and
  [v3](https://2captcha.com/api-docs/recaptcha-v3) docs show a
  **byte-identical** solution for both kinds —
  `gRecaptchaResponse` + `token` (no `score` in either). Shape-only
  dispatch is therefore impossible; the 2026-08-28 "v3 fix" (classify
  `gRecaptchaResponse`+`token` as v3) was itself built on the false
  premise that v2 answers carry `gRecaptchaResponse` alone.
- The same latent collision exists on Anti-Captcha/CapMonster/Capsolver,
  which detect v3 by the `score` key alone.
- Task-11's future-task note had already prescribed the remedy:
  "thread challenge-kind context into status parsing (engine change)
  rather than guessing from keys."

### Done

- **Engine threads kind context.** `parse_submit_response` /
  `parse_task_status` and the compat base's `_solution_from` accept an
  optional keyword-only `challenge_type: type[BaseChallenge] | None`.
  The sync and async engines pass `type(challenge)` at submit and
  `ticket.challenge_type` while polling, so adapters see the submitted
  kind. `wait_ref()` / `get_task_status()` keep the shape fallback (a
  bare `TaskRef` has no kind) — the documented boundary.
- **`TaskTicket.challenge_type`** carries the class into the two-phase
  `submit()` → `wait()` path; the ticket stores the class, never the
  challenge instance, so proxy credentials cannot leak through reprs or
  pickles.
- **All four adapters** treat the challenge kind as authoritative for the
  reCAPTCHA v2/v3 collision, keeping shape dispatch as fallback. The
  2Captcha `_solution_from` no longer classifies `gRecaptchaResponse` +
  `token` as v3 when the submitted challenge was v2.
- Tests: adapter-level kind-context cases for all four adapters, plus
  facade regressions — sync `solve_recaptcha_v2(invisible=True)`, sync
  `solve_recaptcha_v3`, two-phase `submit`/`wait`, and the async facade —
  all mocked with the identical v2/v3 shape.
- Docs/spec: ADR-0079 (`spec/docs/ADR/0079-challenge-kind-context-in-parsing.md`),
  index row, ADR-0053/0067 status amendments, and CHANGELOG entries.

### Verification

- **Live (the original repro):** same script against
  `api.rucaptcha.com` with the live Semrush sitekey now prints
  `type: TwoCaptchaRecaptchaV2Solution` (token 2297 chars; raw answer
  keys `cookies`, `gRecaptchaResponse`, `token`). One real solve, billed.
- `ruff check` / `ruff format --check` / `mypy unicaptcha` /
  `pyright unicaptcha` / `slotscheck unicaptcha`: clean.
- `pytest`: 583 passed, 7 deselected.

### Future-task notes

- [open] Bigger v2/v3 collision risk: if a provider ever returns a v3
  answer with **no** `score` and no engine kind context (e.g. a bare
  `get_task_status(ref)`), it still falls back to shape dispatch. The
  `TaskRef` carries no kind; a future option is to persist the kind in
  the abandoned-task registry so status queries can be kind-aware too.
- [open] Token-only kinds (hCaptcha/Turnstile/FunCaptcha) have the same
  class of ambiguity; all three expose `.token`, so user code works, but
  the type label can be wrong on bare refs. ADR-0079 now gives adapters
  the context to fix it for `solve()`, but the adapters only apply it to
  reCAPTCHA v2/v3 so far.
- [open] 2Captcha v2 answers also carry `cookies` in the
  solution; the universal `RecaptchaV2Solution` has no field for them.
  Not needed for the reported flow (the token is what callers submit),
  but worth recording if worker cookies become user-facing.
