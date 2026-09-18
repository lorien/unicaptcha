## Report on task: Version-pin tests read CHANGELOG.md

### Task (ad-hoc, follow-up to the 0.2.0 release)

`tests/test_package.py::test_version` and
`tests/test_root.py::TestRootExports::test_version` hardcoded the current
version string (`"0.2.0"`), so every release commit had to edit them and a
missed edit turned CI red with no signal from `release_check` (which only
checks tag/version/CHANGELOG).

### Done

- New `released_version` fixture in `tests/conftest.py`: parses the newest
  released `## [x.y.z]` heading from `CHANGELOG.md` (the `[Unreleased]`
  heading is not matched).
- Both version tests now assert `unicaptcha.__version__ == released_version`,
  so a release is consistent in one place: bump `_version.py` + cut the
  changelog section; the tests follow.

Purely internal (tests only) — no `CHANGELOG.md` entry, per the
index.md convention.

### Verification

- `pytest tests/test_package.py tests/test_root.py tests/test_release_check.py`:
  19 passed.
- `scripts/check.sh`: 583 passed / 7 deselected; ruff/format/mypy/pyright/
  slotscheck clean.

### Future-task notes

- [open] The two tests still duplicate the check; the fixture centralizes
  the parsing but both call sites remain (kept, since each module is a
  distinct root-export/package guard).
- [open] `scripts/release_check.py` could reuse the same "newest released
  section" helper for its presence check; it currently only requires the
  versioned section to exist, which is sufficient for the tag guard.
