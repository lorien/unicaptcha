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

## Done

- Verified `pyproject.toml` resolves via `uv sync` (hatchling, version
  single-sourced from `_version.py`, dev group intact).
- Fixed two toolchain gaps that blocked green checks on the empty tree:
  - `[tool.ruff.format] exclude = ["*.md", "*.markdown"]` — ruff 0.16
    also formats code blocks inside Markdown, which would rewrite the
    deliberately aligned pseudo-code in the ADRs.
  - `[tool.pyright] include = ["unicaptcha"]` — bare `pyright` otherwise
    analyzed the gitignored `var/repo/` competitor checkouts (19k errors).
- Created package layout: `unicaptcha/py.typed`, empty `challenge/`,
  `solution/`, `_internal/`, `provider/` (twocaptcha/anticaptcha/
  capmonster/capsolver) subpackages.
- Root `__init__.py`: docstring + `__version__` re-export from
  `_version.py`, `__all__` scaffold (surface grows in later tasks).
- `tests/test_package.py`: parametrized import test over all subpackages
  + `__version__ == "0.1.0"` smoke test (minimal scaffold; full test
  scaffold is task 15). Without it `pytest` errors on the missing
  `tests/` dir (testpaths).
- `.github/workflows/ci.yml`: blocking matrix Python {3.11,3.12,3.13,3.14}
  x {ubuntu, macos}, `fail-fast: false`, running ruff check, ruff format
  --check, mypy, pyright, slotscheck, pytest; separate informational
  3.14t x ubuntu job with `continue-on-error: true` (ADR-0047). No
  coverage flags and no release-consistency tag job (coverage -> deferred
  #21; release job already scoped to task 18).
- Wheel build verified: `py.typed` bundled, `unicaptcha-0.1.0-py3-none-any.whl`.
- All checks green (ruff, mypy strict, pyright strict, slotscheck, pytest
  9 passed). No hard-coded credentials (none exist).