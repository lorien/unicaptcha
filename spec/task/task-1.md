# Task 1: Toolchain + package scaffold

Status: new

Set up the build and package skeleton:

- `pyproject.toml` already declares hatchling, version single-sourced from
  `unicaptcha/_version.py`, and the dev group (ruff, mypy, pyright, pytest,
  pytest-asyncio, respx, pytest-cov, slotscheck) — verify it resolves and
  that all checks pass on the empty tree.
- Create the package layout: `unicaptcha/` with `_version.py`, `py.typed`,
  and the directory skeleton `challenge/`, `solution/`, `provider/`
  (four provider subpackages), `_internal/`.
- Root `__init__.py` with the curated re-export surface (scaffold; fills
  in as later tasks land).
- CI workflow (GitHub Actions): matrix Python 3.11/3.12/3.13/3.14 x
  {Linux, macOS}, blocking lint + typecheck + tests; 3.14t informational.

References: ADR-0004 (Python 3.11+, strict typing), ADR-0019 (toolchain),
ADR-0036 (package layout/naming), ADR-0046 (version single source),
ADR-0047 (CI matrix + free-threaded).