# ADR-0004: Python version floor and typing policy

**Status:** Accepted (supersedes an initial "Python 3.10+" choice)
**Date:** 2026-08-22, amended 2026-08-23

## Context

The floor must be a Python version that is still officially alive at release
time (2026), and the codebase must satisfy two strict type checkers because
the library's value proposition is typed ergonomics.

An earlier decision set the floor to 3.10, the lowest alive version as of
August 2026. Review showed 3.10 reaches end-of-life in October 2026, two
months after this design session; a library released after that date
supporting an EOL Python is pointless.

## Decision

- **Floor: Python 3.11.** Supported: 3.11, 3.12, 3.13, 3.14 (all alive
  today); CI tests all four (ADR-0047).
- 3.11 is also the version where `asyncio.timeout()` (exception-group-era
  timeout scope) is available, which the engine uses for `total_timeout`
  enforcement.
- **Typing**: fully annotated; ship `py.typed`; CI enforces **mypy strict**
  and **pyright strict**.
- Boundary `Any` (raw JSON parsing) is permitted where genuinely needed;
  both checkers' strict modes allow it at assignment sites without further
  tuning.

## Rationale

- Supporting a Python that dies two months post-release buys nothing and
  costs CI matrix slots and syntax constraints.
- 3.11 aligns the floor with a primitive the design depends on.
- Two checkers: mypy and pyright disagree in useful ways; both strict keeps
  the annotations honest for IDE users (pyright) and CI gates (mypy).

## Alternatives considered

- **3.10 floor**: superseded by this ADR (EOL imminence).
- **3.12/3.13-only**: rejected; unnecessarily excludes alive versions.
- **Single checker**: rejected; cross-checker agreement is a quality signal.
- **PEP 563 / `from __future__ import annotations` specifics**: not needed
  on 3.11+ for this codebase's patterns.
