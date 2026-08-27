# ADR-0022: Manual changelog with CI guards

**Status:** Accepted
**Date:** 2026-08-22

## Context

Changelog options: manual Keep-a-Changelog file, auto-generation from
conventional commits (git-cliff), or none. Release-blocker automation was
requested by the owner ("prevent issuing a release without pending
changelog").

## Decision

- `CHANGELOG.md` in Keep a Changelog format; **manual entries**.
- Workflow: features accumulate under `[Unreleased]` with their PRs; at
  release the section is renamed to the version and a fresh
  `[Unreleased]` opens.
- **CI guards**: the release consistency checks (ADR-0021) assert the
  version being tagged has a corresponding changelog section. A release
  without changelog entries fails before publishing.

## Rationale

- Human-written entries carry the "why"; auto-generated notes read as raw
  commit lists unless commit discipline is enforced (which would need
  commitlint machinery — more process for no v1 payoff).
- Manual + guards converts the discipline risk into an automated
  release-blocker, which was the owner's explicit requirement.

## Alternatives considered

- **git-cliff + conventional commits**: rejected; quality equals commit
  discipline, requires enforcement tooling; can be adopted later for
  drafts.
- **No changelog**: rejected; users cannot see what changed between
  versions without diffing releases.
