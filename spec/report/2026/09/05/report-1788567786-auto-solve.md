## Report on task: Auto mode: HTML page detection + auto solve

### Task (archived from plan.md)

Status: done

The library accepts the source code (HTML) of a page plus the page URL;
it detects which captcha the page uses, extracts the needed tokens
(sitekey / public_key / gt+challenge / captcha_id / ...) from the HTML,
solves the captcha with a suitable provider, and returns an
`AutoSolveResult` the caller can inject into the page's form inputs.

### Done

- New public module `unicaptcha/detect.py`:
  - `detect(html, pageurl) -> tuple[DetectedChallenge, ...]` (DOM order;
    empty when nothing found). `DetectedChallenge{kind, challenge, page,
    signals}`; `challenge` is a kind-base instance ready for `solve()`.
  - `AutoSolveResult` (frozen): `detected` (provenance) + `result:
    TaskResult[BaseSolution]` + `fill: Mapping[str, str]`.
  - `pageurl` required (token is domain-bound); non-str `html` raises
    `TypeError`, empty `pageurl` raises `InvalidChallengeError`.
  - `__repr__` truncates fill values (ADR-0034).
- New stdlib-only scanner `unicaptcha/_internal/_html.py` (`re` +
  `html.unescape`, one left-to-right pass so elements and inline
  `<script>` calls stay in document order; no new deps per ADR-0019).
  Detectable: reCAPTCHA v2 (checkbox + invisible via `data-size` /
  `size:` in `grecaptcha.render`), reCAPTCHA v3 (`grecaptcha.execute(
  'SITEKEY', {...})`; bare `execute()` ignored), hCaptcha (incl.
  `is_invisible`/`rqdata`), Turnstile (incl. `action`/`c_data`/
  `chl_page_data`), FunCaptcha (`data-pkey`), GeeTest v3 (`initGeetest`),
  GeeTest v4 (`initGeetest4`). Image/text excluded (API-driven).
- `Solver.auto_solve` / `AsyncSolver.auto_solve(html, pageurl,
  provider=None, *, time, retry, on_event)` solve the first detected
  captcha via the existing `solve()` path; no-detection raises
  `NoCaptchaDetectedError`. No `index` selection — multi-captcha pages
  use `detect()` + `solve()` (ADR-0077).
- `unicaptcha/_internal/fill.py::build_fill` maps solved solutions to
  DOM selectors: v2/v3 → `#g-recaptcha-response`; hCaptcha →
  `textarea[name=h-captcha-response]`; Turnstile →
  `input[name=cf-turnstile-response]`; GeeTest v3 →
  `#geetest_challenge`/`#geetest_validate`/`#geetest_seccode`; GeeTest
  v4 → `#geetest_lot_number`/`#geetest_pass_token`/`#geetest_gen_time`/
  `#geetest_captcha_output` (official `geetest_<key>` convention,
  verified against GeeTest v4 docs); FunCaptcha → `{}` (Arkose callback,
  not a form field).
- New error: `NoCaptchaDetectedError(UnicaptchaError)` + new
  `ErrorKind.NO_CAPTCHA_DETECTED`, wired into `_KIND_CLASS`,
  `error_from_kind`, `__all__`, and the public exports.
- Repr hygiene fix (surfaced by this feature): provider solution
  subclasses across the four shipped adapters now use `@dataclass(...
  repr=False)` so they inherit the kind base's truncating `__repr__`
  instead of the dataclass-generated one that leaked full tokens
  (ADR-0034). Guard tests added in `tests/test_repr.py`.
- Docs: ADR-0077 written (was referenced but missing), registered in
  `spec/docs/index.md`; goals.md non-goal amended (HTML detection + auto
  solve in scope; browser automation stays out); plan.md record updated
  to the agreed design then archived here; `docs/guides/auto-solve.md` +
  nav entries + `docs/api/detect.md`; CHANGELOG `[Unreleased]` Added
  entry.

### Tests

- `tests/test_detect.py` (23 tests): canned HTML per kind, invisible v2,
  hCaptcha rqdata/size, Turnstile data-*, FunCaptcha iframe, JS
  construction calls, whitespace inside calls, v2-vs-v3 disambiguation,
  multi-instance document order, malformed/empty HTML, attribute entity
  unescaping, argument validation, frozen dataclass.
- `tests/test_auto_solve.py` (15 tests): `build_fill` mapping per kind,
  sync/async auto_solve happy path over respx, provider pinning,
  unknown provider TypeError, no-detection error, closed client,
  bad arguments, repr truncation.
- `tests/test_errors.py`: `test_values` and `_LEAF_KINDS` extended for
  `ErrorKind.NO_CAPTCHA_DETECTED`.
- `tests/test_repr.py`: provider-solution repr truncation guards.

### Verification

`uv run ./scripts/check.sh` — ruff, ruff format, mypy, pyright,
slotscheck, pytest: all pass (545 passed, 7 integration deselected).
`uv run mkdocs build` clean.

### Spec/ADR amendments

- ADR-0077 created (accepted 2026-09-05).
- `spec/docs/index.md`: ADR-0077 registered.
- `spec/docs/goals.md`: non-goal "Browser automation, CAPTCHA detection,
  or page scraping" → "Browser automation or page scraping".

### Future-task notes

- GeeTest v4's five-part answer and its conventional hidden-input names
  were verified against the official docs; pages that use a JS callback
  instead of hidden inputs still work via `result.solution` fields.
- Detection is best-effort: widgets referenced by JS variables the
  library cannot resolve are skipped. If a real-world page pattern
  proves common, extend `unicaptcha/_internal/_html.py` (kept internal
  for that reason).