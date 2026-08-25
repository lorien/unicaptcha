# Task 15: Test scaffold + reference third-party adapter

Status: new

- `tests/` scaffold: conftest, pytest + pytest-asyncio strict mode, respx
  transport mocking, slotscheck, coverage config; integration marker
  (`-m 'not integration'` default).
- Reference third-party adapter **"myservice"** implemented against the
  public API only (ADR-0046); CI-enforced guard that it never imports
  `_internal`.
- Verify all toolchain checks pass (ruff, mypy strict, pyright strict,
  pytest, slotscheck).

References: ADR-0019, ADR-0041, ADR-0046, ADR-0004.