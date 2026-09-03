# Plan

Open tasks. A task is a record with a `##` header (task name), a `Status:`
line, a `Priority:` line, the task body, and an optional `References:`
line.

Statuses:

- `new` — not started; ready to pick up.

Priorities:

- `Priority: N` right after the `Status:` line; default `0` for new
  records. Higher numeric value = more important.
- `Priority: -1` = deferred: the task is not auto-picked until its
  priority is raised.

A `done` task does not live here: when a task is finished, its record is
removed and archived into the report of the session that worked on it
(`spec/report/`). A task leaves plan.md only when its work is complete and
committed.

Selection picks the highest-priority `new` task; ties break by file order,
and `Priority: -1` (deferred) tasks are never auto-picked. The owner edits
`Priority:` values to reprioritize — no physical reordering needed.

Ad-hoc tasks requested directly by the user are not tracked here; their
reports live in `spec/report/`.

## Release-consistency CI guards

Status: new
Priority: -1

Add a `release-check` job to `.github/workflows/ci.yml` running on `v*`
tag pushes: tag == `unicaptcha/_version.py` version == matching
`## [{version}]` CHANGELOG section.

References: ADR-0021, ADR-0022.

## PyPI publishing / release automation

Status: new
Priority: -1

Whether a `v*` tag triggers automated publish, a TestPyPI dry-run, and
trusted publishing vs token. Deliberately postponed.

## Provider selection / failover policy

Status: new
Priority: -1

Kind-level uniform random selection exists (ADR-0064); still open:
*policy* routing — cheapest-first, failover, load balancing,
stickiness/weighting. A strategy wrapper could be a purely additive layer.

## Client-side rate limiting / concurrency caps

Status: new
Priority: -1

No `max_parallel_solves`, no request spacing in v1; callers manage
concurrency and the rate-limit retry with backoff is the safety net.

## API-key rotation

Status: new
Priority: -1

One key per provider instance in v1; rotation as a provider-level wrapper.

## Webhook/pingback solve mode

Status: new
Priority: -1

v1 is strictly poll-based; the submit/await split keeps a webhook mode
additive if ever added.

## Hierarchical logger names

Status: new
Priority: -1

v1 uses one flat `unicaptcha` logger; per-component names
(`unicaptcha.http`, `unicaptcha.provider.twocaptcha`, ...) if
per-component filtering is requested.

## unicaptcha.testing module

Status: new
Priority: -1

Fake clients / canned results / failure injection for downstream test
suites. Defer until the core API survives real usage.

## Capability introspection API

Status: new
Priority: -1

`client.supports(...)` / `providers_supporting(...)` and challenge-kind
tags. v1: probe by calling, catch exceptions.

## Client usage statistics

Status: new
Priority: -1

Cumulative solved/failed counters, Decimal cost totals, per-provider
breakdown; prefer an `on_event`-fed collector over client state.

## Deferred kinds: KeyCaptcha, Capy Puzzle, TikTok

Status: new
Priority: -1

Named candidates excluded from v1 (ADR-0070): single-provider, low
demand, or cookies-typed solutions. Third-party adapters may cover them
via the SDK.

## Deferred providers: DBC, azcaptcha, cap.guru, cptch.net, sctg.xyz, multibot

Status: new
Priority: -1

Named candidates excluded from v1 (ADR-0071): other protocol families or
unverified JSON-API mirrors. RuCaptcha is not here — verified working via
`base_url`.

## Image classification tasks

Status: new
Priority: -1

CapMonster `ComplexImageTask`, Capsolver `*Classification`, NopeCHA
recognition API. Distinct from token-solving kinds; third-party adapters
may cover via the SDK.

## Template automation tasks

Status: new
Priority: -1

Anti-Captcha AntiGate and CapMonster CustomTasks (DataDome, Imperva,
TenDI, ...). Needs a new task model, not a kind.

## Statistics endpoints

Status: new
Priority: -1

`getQueueStats` / `getAppStats` / `getSpendingStats` on the Anti-Captcha
surface; aux ops deliberately stop at balance + good/bad reports.

## CI coverage presentation/gating

Status: new
Priority: -1

pytest-cov stays informational only (ADR-0047); whether CI passes
`--cov`, what reports are shown/uploaded, and if a coverage threshold
becomes a gate — all undecided.

## Test-double consolidation (`_fake`/ScriptedAdapter → `_myservice`)

Status: new
Priority: -1

FakeAdapter + ScriptedAdapter + the reference MyServiceAdapter coexist;
consolidating onto `tests/_myservice.py` would remove triple duplication
of a provider double.

## Shared ErrorKind mapping table

Status: new
Priority: -1

Each adapter carries a private provider-code → ErrorKind dict and the
event tests carry their own kind matrix; hoist one shared table/module so
adapter tests and events cannot drift.

## `_internal/log.py`

Status: new
Priority: -1

A shared module for the flat `unicaptcha` logger if call sites
proliferate (ADR-0018/0039 keep it flat; extract only on need).

## Async clock seam

Status: new
Priority: -1

`Clock.sleep` is sync-only; the async engine sleeps via asyncio directly.
A loop-time injection seam would make async timeout/cadence tests fully
instant (sync tier already has the seam, task 16).

## Universal `solve()` kind overloads

Status: new
Priority: -1

Universal-tier `solve` returns `TaskResult[Any]` statically (runtime fully
typed). Add the nine-kind overload set if universal precision is wanted;
facades already type precisely.

## README snippet verification

Status: new
Priority: -1

README snippets are prose-reviewed only (ADR-0023). Options: execute
snippets with mocked transport or compile-check the fenced blocks (the
examples/ dir already gets compile checks via `tests/test_examples.py`).

## Example demo values: geetest_v3 dynamic challenge; funcaptcha annotation

Status: new
Priority: -1

Live smoke (2026-08-28): geetest_v3 examples fail with `NoSolutionError`
— the static demo `challenge` is stale by design (one-time value). Fetch
a fresh challenge from the 2captcha demo page per run (the vendor SDK
example's pattern: GET the page, `split(';')[0]`) in sync/async examples.
FunCaptcha's public demo blob is not worker-solvable; keep those examples
illustrative with an explicit docstring/README note (`NoSolutionError`
expected).

## Markdown link checker in CI

Status: new
Priority: -1

A README/docs link checker job; cheap, but decide scope (README only vs
spec/docs too) and whether broken-link tolerance is needed for external
URLs.

## Report commit-hash traceability

Status: new
Priority: -1

Whether session/task reports should cite commit hashes for traceability
(undecided; currently reports cite task names and dates only).

## Auto mode: HTML page detection + auto solve

Status: new
Priority: -1

The library accepts the source code (HTML) of a page plus the page
URL; it detects which captcha the page uses, extracts the needed
tokens (sitekey / public_key / gt+challenge / captcha_id / ...) from
the HTML, solves the captcha with a suitable provider, and returns an
`AutoSolveResult` the caller can inject into the page's form inputs.

Design (ADR-0077):
- New public module `unicaptcha/detect.py`: `detect(html, pageurl) ->
  tuple[DetectedChallenge, ...]` (DOM order; empty tuple when nothing
  found). `DetectedChallenge{kind, challenge, page, signals}`.
- Stdlib-only parsing (`html.parser.HTMLParser` + `re` + `html.unescape`)
  in `_internal/_html.py`; no new runtime deps (ADR-0019).
- Detectable kinds: reCAPTCHA v2 (incl. invisible), reCAPTCHA v3
  (render= / grecaptcha.execute), hCaptcha, Turnstile (incl. action /
  c_data / chl_page_data), FunCaptcha (data-pkey), GeeTest v3
  (initGeetest), GeeTest v4 (initGeetest4). Image/text excluded
  (API-driven, not HTML-detectable). v2 vs v3 disambiguated by
  render=/execute; both present -> two detections.
- `Solver.auto_solve` / `AsyncSolver.auto_solve(html, pageurl,
  provider=None, *, index=0, time=None, retry=None, on_event=None) ->
  AutoSolveResult`: solves detected[index] via the existing solve()
  path (ADR-0064 dispatch; provider= pins).
- `AutoSolveResult` (frozen): `result: TaskResult[BaseSolution]` +
  `fill: Mapping[str, str]` — default selector->value per kind
  (#g-recaptcha-response, textarea[name=h-captcha-response],
  input[name=cf-turnstile-response], #geetest_challenge/
  #geetest_validate/#geetest_seccode; GeeTest v4 field names verified
  during implementation; none for FunCaptcha). Caller applies to the
  live DOM (no browser).
- New error `NoCaptchaDetectedError(UnicaptchaError)` on no detection.
- pageurl is a required argument: serialized as websiteURL in the
  payload; the returned token is bound to that domain.
- goals.md non-goal amended: HTML detection + auto solve in scope;
  browser automation stays out.
- Tests: tests/test_detect.py (canned HTML per kind, multi-instance,
  v2/v3, malformed HTML), tests/test_auto_solve.py (respx end-to-end,
  uniform_choice monkeypatch, fill mapping).

References: ADR-0077.