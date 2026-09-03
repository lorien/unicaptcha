## Report on task: Rename JsonAdapterBase to reflect the submit-poll protocol family

### Task (archived from plan.md)

Status: done

`JsonAdapterBase` (committed 2026-08-31) is too generic: the name
implies a base for any JSON API, but it is the shared base for the
`createTask`/`getTaskResult` submit→poll→result captcha-provider
protocol family (ADR-0001) — a design all captcha providers mimic
(submit → poll → get, plus balance/reports). Rename to a name that
states the design, not the encoding:

- `SubmitPollAdapterBase` (recommended — matches the existing
  submit/poll vocabulary: ADR-0067 two-phase submit/wait, ADR-0011
  polling policy, the `submit()`/`wait()` methods).
- `TaskQueueAdapterBase` (model-flavored alternative).

Touch points: `unicaptcha/adapter.py` (class name, `__all__`,
docstring wording), `unicaptcha/__init__.py`, the four provider
adapters (import + subclass line), `tests/test_package.py`,
`spec/docs/architecture.md` §9 (the added layout-tree / public-surface /
adapter-SDK wording, aligned to submit→poll / `createTask`–`getTaskResult`),
and `CHANGELOG.md` (Unreleased Changed entry). The historical session
report `spec/report/2026/08/31/report-1788185812-json-adapter-base.md`
is not rewritten (historical records stay as-is). Pick the name on
execution, then run the full verification suite.

References: ADR-0001.

### Done

- Renamed `JsonAdapterBase` → `AntiCaptchaCompatAdapterBase` (chosen on
  execution). Web research established Anti-Captcha as the documented
  originator of the `createTask`/`getTaskResult` JSON protocol: Wayback
  snapshots show Anti-Captcha's task-based API v2 existed by 2016
  (legacy `in.php`/`res.php` predates it); CapMonster Cloud's own 2021
  FAQ lists "Anti-Captcha (v1.0, v2.0)" among the APIs it *emulates*
  (drop-in compatible); independent sources name the family the
  "Anti-Captcha-compatible API". The chosen name signals the protocol
  family (not the encoding, not the generic submit/poll pattern), and
  the "Compat" suffix avoids the collision reading with the concrete
  `AntiCaptchaAdapter`.
- `unicaptcha/adapter.py`: class renamed, docstring reworded to the
  protocol-family framing, `__all__` updated.
- `unicaptcha/__init__.py`: import and alphabetical `__all__` entry.
- The four provider adapters (import + subclass line):
  twocaptcha, anticaptcha, capmonster, capsolver.
- `tests/test_package.py`: import, `issubclass` guard, abstract guard;
  test names reworded from the "json" framing.
- Docs: `spec/docs/architecture.md` §9 (layout-tree line, public-surface
  bullet, Adapter SDK snippet, endpoints comment), `CHANGELOG.md`
  Unreleased Changed entry.
- Historical session report `report-1788185812-json-adapter-base.md`
  left as-is.

### Verification

`uv run ruff check .` / `uv run mypy unicaptcha` / `uv run pytest` —
all pass (integration deselected).

### Spec/ADR amendments

None. The plan's original name suggestions (`SubmitPollAdapterBase` /
`TaskQueueAdapterBase`) were superseded by the evidence-backed protocol
family naming; ADR-0001 wording ("JSON-family") is unchanged in the ADR
itself.

### Future-task notes

- The base's `json_provider` ClassVar (error-message display label) is a
  leftover "json" word; candidate follow-up if the "JSON-family"
  vocabulary is purged everywhere (spec/docs + code).
- `tests/_myservice.py` (reference adapter) still subclasses
  `BaseAdapter` directly; it could now subclass
  `AntiCaptchaCompatAdapterBase` as the documented third-party pattern
  (open since the JSON-adapter-base session).

### Tooling/process

- Provenance research method that worked: Wayback CDX API
  (`web.archive.org/cdx/search/cdx`) for earliest docs snapshots, plus
  provider FAQ/landing pages archived in Wayback, plus independent
  third-party comparisons (uCaptcha, dolphin-anty, CapSkip, Bright Data).
  The Medium article claiming Anti-Captcha's model is "similar to
  CapMonster" was checked and outweighed by the direct evidence above.