# ADR-0047: CI matrix and free-threaded Python

**Status:** Accepted (amended 2026-09-05: the matrix runs the canonical
`scripts/check.sh` — one command, local/CI parity; tool selection unchanged)
**Date:** 2026-08-23

## Context

CI must cover the supported Python range (3.11-3.14, all alive), decide
OS coverage, coverage gating, and — owner-proposed — free-threaded
(GIL-less) Python. The dependency stack being pure Python (httpx and
below; pydantic was dropped), free-threaded compatibility risk is low and
the value real: the sync client's documented thread-safety guarantee
(ADR-0027) gets exercised without the GIL masking races.

## Decision

- **Blocking matrix**: Python {3.11, 3.12, 3.13, 3.14} x {Linux, macOS},
  running the canonical `scripts/check.sh` (lint, mypy, pyright, slotscheck,
  tests). The script is the single definition of the check set; the matrix
  step and the local workflow (see `testing.md`) both invoke it, so local
  and remote cannot drift apart.
- **Free-threaded**: 3.14t x Linux as a separate **informational** job
  (`continue-on-error: true`). 3.13t skipped (experimental, superseded
  by 3.14t per PEP 779). Promotion to blocking after a few stable green
  releases.
- **Coverage**: pytest-cov, informational only — no enforced threshold
  while experimental (gates during heavy refactoring breed
  coverage-gaming).
- **Windows**: not in matrix; respx-mocked suite makes it low-value now;
  add on real-user demand.
- Release consistency checks (ADR-0021, ADR-0022) run on tag events.

## Rationale

- Four alive interpreters cost near-zero in GH Actions and continuously
  validate the 3.11 floor claim.
- 3.14t as informational: signal without red-build noise while the
  free-threaded ecosystem stabilizes.
- Informational coverage keeps honesty (visible number) without the
  gate's perverse incentives.

## Alternatives considered

- **Linux-only**: rejected; macOS is cheap and catches platform
  assumptions.
- **+ Windows from day one**: rejected; slow, historically flaky for
  socket-adjacent tests, no current demand.
- **Coverage threshold (e.g. 90%)**: rejected for experimental phase.
- **3.13t in matrix**: rejected; superseded artifact.
