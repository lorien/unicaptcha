# Provider fidelity verification (2026-08-28 pass)

Evidence: the wire-contract diff matrix in [fidelity.md](../../../docs/fidelity.md)
(vendor clones at the HEADs recorded there) plus a full live smoke run
against real 2Captcha workers (same service as RuCaptcha; key used
against `api.2captcha.com` directly).

### Done

- Triage of all 58 `[open]`/`[needs-decision]` markers in `spec/report/`:
  11 refactor/tooling themes became new `Priority: -1` records in
  `spec/docs/plan.md`; wire-row `[needs-decision]` markers folded into the
  fidelity checklist; stale items (CapMonster repo URL — verified by
  cloning it; CI-env notes) dismissed.
- Docs-drift fixes applied: architecture §1 HTTP-layer row (retry policy
  moved to engines), §5 `abandoned_registry_limit` sketch default 1000,
  ADR-0075 TaskTicket `time:` field pinned, ADR-0053
  `build_task_status`/`build_balance` row, ADR-0067 `wait_ref` default
  budget pin.
- `spec/docs/fidelity.md` written: repeatable verification algorithm,
  per-provider evidence rules, 35-row verification matrix, re-run recipe.
- Static pass: 34 rows verified against vendor sources, 1 discrepancy
  **fixed** — CapMonster GeeTest v4 now sends `gt` = captcha id +
  `initParameters.riskType` only (vendor SDK requires `gt`
  unconditionally; `examples/geeTestv4.py` attests); golden fixture and
  tests regenerated from the vendor-derived expectation.
- Live smoke, full matrix (all 7 integration tests + all 20 sync/async
  examples against real workers):

| Kind | sync | async | Notes |
|---|---|---|---|
| image | pass | pass | |
| text | pass* | pass | *needs budget override — see finding 1 |
| reCAPTCHA v2 | pass | pass | |
| reCAPTCHA v3 | pass | pass | after finding-2 fix (first run crashed) |
| hCaptcha | pass | NoSolutionError | test-key solves are flaky provider-side |
| FunCaptcha | NoSolutionError | NoSolutionError | demo blob not worker-solvable (example-values limitation) |
| GeeTest v3 | NoSolutionError | NoSolutionError | static demo `challenge` is stale by design (dynamic per docs) |
| GeeTest v4 | pass | pass | |
| Turnstile | pass | pass | |
| universal client | pass | pass | |
| two_phase / aux_ops / events / errors / proxy | pass | — | facade ops verified end-to-end |

- `NoSolutionError` outcomes are correct library behavior (task created,
  polled, workers reported unsolvable); they record example-value
  limitations, not adapter bugs.

### Spec/ADR amendments

- [acted] ADR-0030's text-kind default budget (30 s) is too tight for
  real workers: two consecutive live text solves exceeded it; the same
  solve passed with `total_timeout=180`. Filed as a new plan.md record
  (kind timing defaults revisit) rather than amending the ADR unilaterally.
- [acted] `fidelity.md` live-only notes updated: v3 solution shape now
  live-verified (`gRecaptchaResponse` + `token`, no `score`).

### Future-task notes

- [open] Turnstile-vs-hCaptcha solution ambiguity stands (both return
  `token`-only shapes; adapter classifies token-only as hCaptcha). Both
  expose `.token` so user code works; the type label can be wrong
  (pre-existing audit marker, still open).
- [open] `tests/test_examples.py` only `compile()`s examples — it missed
  a facade-attribute misuse in `examples/sync/proxy.py` that the live run
  caught. An import-and-attribute smoke (or running examples against the
  mocked transport) would close this; relates to the plan records
  "README snippet verification" and example verification.

### Tooling/process

- [acted] Fixed during the smoke: `examples/sync/proxy.py` called the
  facade's nonexistent generic `solve()`; now uses `solve_image`.
- [acted] Fixed during the smoke: 2Captcha `_solution_from` classified
  the live-verified v3 shape (`gRecaptchaResponse` + `token`, no score)
  as a v2 solution; v3 is now recognized by the `token` co-presence
  (score `None`). Unit-tested.
- Live smoke recipe that worked: `UNICAPTCHA_TWOCAPTCHA_API_KEY=$(tr -d
  '[:space:]' < ~/.keys/rucaptcha.key) uv run pytest -m integration
  tests/test_live_twocaptcha.py` and the same env prefix per example run;
  capture each run's output to a file — pipeline exit codes lie (`$?` is
  `tail`'s).
