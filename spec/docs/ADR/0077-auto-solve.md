# ADR-0077: Auto mode — HTML page detection + auto solve

**Status:** Accepted
**Date:** 2026-09-05

## Context

Callers currently must know the captcha a page uses before they can solve
it: pick a challenge class, extract the sitekey / public_key /
gt+challenge / captcha_id from the page, and pass it to `solve()`. A
page's captcha is discoverable from its HTML, and the discovery is the
same across providers — it belongs in the library so the caller can hand
it a page and get a solved, fill-ready answer.

The library's non-goals have kept browser automation and page scraping
out (goals.md); this ADR keeps that boundary: the library reads the
page's *source code* only and never drives a browser.

## Decision

- **New public module `unicaptcha/detect.py`:**
  `detect(html, pageurl) -> tuple[DetectedChallenge, ...]` in DOM order;
  empty tuple when nothing is found.
  `DetectedChallenge{kind, challenge, page, signals}` — `challenge` is a
  kind-base instance ready for `solve()` (pageurl bound), `signals` the
  human-readable evidence that matched.
- **Stdlib-only parsing** (`html.parser`/`re`/`html.unescape`) in
  `unicaptcha/_internal/_html.py`; no new runtime dependencies
  (ADR-0019). One left-to-right pass keeps element widgets and inline
  `<script>` construction calls in document order.
- **Detectable kinds**: reCAPTCHA v2 (checkbox + invisible), reCAPTCHA
  v3, hCaptcha, Turnstile, FunCaptcha (`data-pkey`), GeeTest v3
  (`initGeetest`), GeeTest v4 (`initGeetest4`). Image/text are
  API-driven, not HTML-detectable, and stay out. v2 vs v3 is
  disambiguated by `render=`/`execute('SITEKEY', ...)`; both present
  produce two detections.
- **`Solver.auto_solve` / `AsyncSolver.auto_solve(html, pageurl,
  provider=None, *, time=None, retry=None, on_event=None) ->
  AutoSolveResult`**: detects, solves the *first* match via the existing
  `solve()` path (ADR-0064 dispatch; `provider=` pins). No `index`
  selection: multi-captcha pages use `detect()` + `solve()` explicitly.
  No detection raises `NoCaptchaDetectedError`.
- **`AutoSolveResult`** (frozen): `detected: DetectedChallenge` (what was
  solved and why), `result: TaskResult[BaseSolution]`,
  `fill: Mapping[str, str]` — the DOM selector → solved-value map the
  caller injects into the live page (no browser built in).
- **Fill table** (per kind; FunCaptcha has no standard injectable field
  and yields `{}` — its token goes through the page's Arkose callback):
  reCAPTCHA v2/v3 → `#g-recaptcha-response`; hCaptcha →
  `textarea[name=h-captcha-response]`; Turnstile →
  `input[name=cf-turnstile-response]`; GeeTest v3 →
  `#geetest_challenge`/`#geetest_validate`/`#geetest_seccode`; GeeTest v4
  → `#geetest_lot_number`/`#geetest_pass_token`/`#geetest_gen_time`/
  `#geetest_captcha_output` (official `geetest_<key>` convention,
  verified against GeeTest v4 docs during implementation).
- **New error** `NoCaptchaDetectedError(UnicaptchaError)` mapped 1:1 to a
  new `ErrorKind.NO_CAPTCHA_DETECTED`.
- **`pageurl` is required**: serialized as the token's `websiteURL`; the
  returned token is bound to that domain.
- **Representation safety**: `AutoSolveResult.__repr__` truncates fill
  values (ADR-0034); provider solution subclasses gained `repr=False` so
  they inherit the kind base's truncating repr instead of the
  dataclass-generated one that leaked full tokens.

## Rationale

- One convenience entry point for the dominant single-captcha case; the
  fully-typed `detect()` + `solve()` path stays available and discoverable
  for multi-captcha pages.
- Stdlib-only keeps the dependency surface flat (ADR-0019); parsing is
  deliberately best-effort — a widget referenced by a JS variable the
  library cannot resolve is skipped, never an error.
- `fill` is a plain mapping so the caller's own browser layer (Playwright,
  Selenium, ...) applies it; the library stays browser-free (goals.md).

## Alternatives considered

- **`index=` to select among several detections in `auto_solve`**:
  rejected — the number is opaque without a prior `detect()` call, and
  callers who have that information can call `solve()` directly.
- **Solve all detections and return a tuple**: rejected — multi-solve
  cost surprise and a clumsier single-captcha API.
- **DOM-field injection API taking a live page object**: rejected —
  browser coupling contradicts the non-goal.

## Amendments

- goals.md non-goal amended: "Browser automation, CAPTCHA detection, or
  page scraping" → "Browser automation or page scraping" (HTML detection
  + auto solve are now in scope; browser automation is not).