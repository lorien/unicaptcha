# ADR-0021: Static SemVer versioning

**Status:** Accepted
**Date:** 2026-08-22

## Context

Version management options: static version in `pyproject.toml` bumped
manually per release, or dynamically derived from git tags
(uv-dynamic-versioning). The project will have infrequent, deliberate
releases. Starting version must signal experimental status.

## Decision

- **SemVer**, starting at **0.1.0**. The 0.x line signals "API may change
  freely"; the project additionally declares itself experimental with no
  stability obligations even on the public surface (goals.md).
- **Static mechanism**: version lives in `unicaptcha/_version.py`
  (single source; pyproject reads it via hatch, ADR-0046) and is bumped
  manually per release.
- **CI consistency checks** guard the manual process: on a `v*` tag, CI
  asserts tag name == version == a matching CHANGELOG section. Drift
  becomes unpublishable. A local `release-check` script may run the same
  assertions.

## Rationale

- Static + checks beats dynamic plugins at this release cadence: dynamic
  versioning shines with many unreleased commits between tags; here the
  "two places to update" burden is fully covered by automation.
- Single-source `_version.py` avoids pyproject/`__version__` drift while
  keeping `unicaptcha.__version__` importable without
  `importlib.metadata`.

## Alternatives considered

- **Git-tag-driven dynamic versioning**: rejected; extra build plugin,
  requires full git checkout to build, dev-suffix versions unnecessary at
  this cadence.
- **Version only in pyproject**: superseded by the single-source
  `_version.py` refinement (ADR-0046).
- **Start at 1.0.0**: rejected; nothing is stable.
