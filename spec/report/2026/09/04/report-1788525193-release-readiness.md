## Report on task: Release readiness (CI guards + publishing + coverage)

Ad-hoc owner chapter: three release-readiness tasks worked together
(tasks 1-3, discussed one by one; owner decisions recorded below).

### Task 1 (archived from plan.md): Release-consistency CI guards

Status: done

Add a `release-check` job to `.github/workflows/ci.yml` running on `v*`
tag pushes: tag == `unicaptcha/_version.py` version == matching
`## [{version}]` CHANGELOG section.

References: ADR-0021, ADR-0022.

### Task 2 (archived from plan.md): PyPI publishing / release automation

Status: done

Whether a `v*` tag triggers automated publish, a TestPyPI dry-run, and
trusted publishing vs token. Deliberately postponed.

### Task 3 (archived from plan.md): CI coverage presentation/gating

Status: done

pytest-cov stays informational only (ADR-0047); whether CI passes
`--cov`, what reports are shown/uploaded, and if a coverage threshold
becomes a gate — all undecided.

### Done

- **`scripts/release_check.py`** — single source for the ADR-0021/0022
  assertions: `tag == f"v{__version__}"` (from `unicaptcha/_version.py`)
  and `CHANGELOG.md` contains `^## [<version>]` (**presence only**,
  owner decision — the date suffix is cosmetic, not a release blocker).
  Reads `GITHUB_REF_NAME` or `--tag`; `exit(1)` on mismatch; runnable
  locally (`python scripts/release_check.py --tag v0.1.0`).
- **ci.yml** — new `release-check` job on `v*` tag pushes only (owner
  decision; avoids transient false alarms between a version bump and the
  changelog rename): runs the script + `uv build` (owner decision: a
  broken build at tag time blocks the release). Also added
  `--cov=unicaptcha --cov-report=term-missing` to the `test` job
  (coverage visible in every leg's log; informational only — no gate per
  ADR-0047, no external service, no HTML artifact; owner decision).
- **`.github/workflows/publish.yml`** — on `v*` tags: `release-check`
  job (shared script) then `publish` job (`needs:`), which `uv build`s,
  `twine check`s, and runs `pypa/gh-action-pypi-publish@release/v1`
  (`attestations: true`, trusted publishing / OIDC) gated behind the
  `PUBLISH_ENABLED` repo variable. **Build + `twine check` only for now**
  (owner decision) — the upload is a one-line flip once the owner creates
  the PyPI project and configures the trusted publisher.
- **pyproject.toml** — `twine` added to the dev group.

### Verification

`scripts/release_check.py` — `--tag v0.1.0` exits 1 today (no
`## [0.1.0]` section), `--tag v0.2.0` exits 1 (version mismatch), no tag
exits 1; all messages clear. Both workflow YAMLs parse. `uv build`
produces wheel + sdist. `uv run pytest --cov=unicaptcha
--cov-report=term-missing` passes (497 / 7, 87% coverage, term-missing
report). `ruff check` / `format --check` clean (script included).

### Spec/ADR amendments

None required: ADR-0021/0022 already specified the guard; ADR-0047
already fixed the coverage policy (informational, no gate). The
presentation decisions are recorded here.

### Future-task notes

- **Owner-side (cannot do from code)**: create the `unicaptcha` PyPI
  project + trusted-publisher config (trust `lorien/unicaptcha` tags),
  then set the `PUBLISH_ENABLED` repo variable to flip the upload on.
- **After the first real publish**: revert the install docs from
  `git+https://...` back to plain `uv add unicaptcha` /
  `pip install unicaptcha` (the "once published" promise in README +
  getting-started).
- `release-check` on tags also runs `uv build`; the publish workflow
  rebuilds for its artifacts — minor duplication, acceptable.

### Tooling/process

- Discussed the three tasks one by one (ordering: task 1 gates task 2;
  task 3 independent); all decisions made explicitly by the owner.