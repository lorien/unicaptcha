# Releasing

How to cut a release: what must agree before a `v*` tag, the one-time
PyPI setup, the per-release steps, and what CI enforces. The consistency
guards (ADR-0021, ADR-0022) make a drifted release unpublishable.

## The consistency rule

On any `v*` tag, `scripts/release_check.py` asserts three things agree:

- the tag name equals `f"v{unicaptcha._version.__version__}"`;
- `CHANGELOG.md` has a `## [<version>]` section (presence only — the date
  suffix is cosmetic, not a release blocker).

If they do not agree, both the CI `release-check` job and the Publish
workflow fail and nothing is uploaded. Run the check locally before
tagging:

```
uv run python scripts/release_check.py --tag v0.1.0
```

## One-time setup (owner-side, cannot be done from code)

1. Create the `unicaptcha` project on https://pypi.org — the name must
   match `[project] name` in `pyproject.toml`.
2. Configure **trusted publishing** (no stored token): PyPI → account →
   Publishing → Add a pending publisher → GitHub:
   - Owner: `lorien`
   - Repository: `unicaptcha`
   - Workflow file name: `.github/workflows/publish.yml`
   - Environment name: `pypi`
3. Enable the upload: GitHub → Settings → Secrets and variables →
   Actions → Variables → repository variable `PUBLISH_ENABLED = true`.
   Until this is set, the publish job only builds and `twine check`s —
   nothing is uploaded.

## Per release

1. Bump `unicaptcha/_version.py` (`__version__`) if it changed since the
   last release.
2. `CHANGELOG.md`: rename `## [Unreleased]` → `## [<version>] - <date>`
   and open a fresh `## [Unreleased]` at the top.
3. Local sanity: `uv run python scripts/release_check.py --tag v<version>`
   → prints `release-consistent`.
4. Commit (e.g. `Prepare release <version>`) and push to `main`.
5. Tag and push:
   ```
   git tag v<version>
   git push origin v<version>
   ```
6. Watch GitHub Actions:
   - **CI**: the `test` matrix and `docs` are green (`docs` is main-only,
     so tag pushes skip it); `release-check` is green.
   - **Publish**: `release-check` green → `uv build` → `twine check` →
     upload to PyPI (trusted publishing, attestations) when
     `PUBLISH_ENABLED`.
7. Verify on PyPI: the wheel and sdist for `<version>` are published; a
   fresh-venv `pip install unicaptcha==<version>` works.

## After release

- (Optional) Create a GitHub Release at the tag, drafted from the
  changelog section.
- Next cycle: features accumulate under the new `## [Unreleased]`;
  `_version.py` is bumped at the next release.

## Notes

- The CI workflow goes red on any `v*` tag that is not release-consistent
  — intended.
- Optional extra safety: publish to TestPyPI first
  (`repository-url: https://test.pypi.org/legacy/`) before flipping to
  real PyPI.
- First-release special case (v0.1.0): the install docs temporarily used a
  `git+https` form and were reverted to the plain PyPI form once the
  package was live. Not a per-release step.