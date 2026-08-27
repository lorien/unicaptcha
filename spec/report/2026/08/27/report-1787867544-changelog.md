## Report on task: CHANGELOG: v1 Unreleased summary

### Task (archived from plan.md)

```
## CHANGELOG: v1 Unreleased summary

Status: done

Fill CHANGELOG.md `[Unreleased]` with the v1 implementation summary
(universal + facade clients, four providers, nine-kind taxonomy, unified
errors, configs, two-phase submit/wait, aux operations, adapter SDK,
events/logging, abandoned-task registry, strict-typing toolchain); static
version stays 0.1.0.

References: ADR-0021, ADR-0022.
```

### Done

- Filled `CHANGELOG.md` `[Unreleased]` → `### Added` with a user-facing v1
  summary: universal + facade clients, four provider adapters, nine-kind
  taxonomy, unified error hierarchy, typed configs, two-phase submit/await
  (incl. the submit-ready fast path), aux operations, adapter SDK, events/
  logging, abandoned-task registry, strict-typing toolchain, base-URL
  mirrors and referral. Version stays static 0.1.0; no `## [0.1.0]`
  section created yet. Dropped the pre-existing internal "Project
  knowledge base" bullet (not user-facing).
- Persisted two changelog conventions in `spec/docs/index.md` →
  `## Conventions`:
  1. User-facing docs (`README.md`, `CHANGELOG.md`) never cite ADRs.
  2. Every task that changes user-facing behavior adds an entry under
     `CHANGELOG.md` `[Unreleased]`; internal-only tasks skip it with a
     one-line note in their report.
- Removed the four ADR parenthetical citations from `README.md`
  (`(ADR-0064)`, `(ADR-0065)`, `(ADR-0071)`, `(ADR-0072)`) — the README is
  user-facing and now cites no ADRs, per the new convention.
- Verification: `uv run pytest` (452 passed), `uv run ruff check .`,
  `uv run ruff format --check .`, `uv run mypy unicaptcha`,
  `uv run pyright unicaptcha`, `uv run slotscheck unicaptcha` — all clean.

### Spec/ADR amendments

- None; the conventions live in `spec/docs/index.md` (not in an ADR), and
  the changelog itself stays ADR-free by convention.

### Future-task notes

- The remaining split sub-task "Release-consistency CI guards" is still
  open in `plan.md`; when implemented, its release-check job must read the
  version from `unicaptcha/_version.py` and assert a matching
  `## [{version}]` CHANGELOG section exists.

### Tooling/process

- [acted] Changelog conventions are now recorded in `spec/docs/index.md`
  `## Conventions` (per owner): no ADR citations in user-facing docs, and
  user-facing changes always get an `[Unreleased]` entry. The conventions
  live in `spec/docs/` on purpose — `spec/skills/*` stays generic.