## Report on task: Shared ErrorKind mapping table

### Task (archived from plan.md)

Status: done

Each adapter carries a private provider-code → ErrorKind dict and the
event tests carry their own kind matrix; hoist one shared table/module so
adapter tests and events cannot drift.

### Done

- New `tests/_error_kinds.py` (shared, not collected): `PROVIDER_ERROR_KINDS`
  — the expected `errorCode` → `ErrorKind` tables for the four shipped
  providers (twocaptcha, anti-captcha, capmonster, capsolver), mirroring
  each adapter's `error_kinds` ClassVar — and `TERMINAL_ERROR_KINDS` —
  the events terminal-kind matrix moved verbatim from `test_events.py`.
- New `tests/test_error_kinds.py` (5 tests):
  - `test_adapter_error_kinds_match_shared_table` (parametrized ×4):
    `adapter.error_kinds == PROVIDER_ERROR_KINDS[adapter.provider]` — the
    test-side table is authoritative; editing an adapter without updating
    the shared table fails.
  - `test_mapped_kinds_are_valid_terminal_event_kinds`: every mapped kind
    must be a valid `SUBMIT_FAILED` terminal kind — the adapter→events
    drift guard (holds today: AUTHENTICATION / RATE_LIMIT /
    SERVICE_BUSY / INSUFFICIENT_BALANCE ⊆ SUBMIT_FAILED).
- `test_twocaptcha.py::test_map_provider_error_table` now iterates
  `PROVIDER_ERROR_KINDS["twocaptcha"]` instead of re-typing the table
  inline (keeps message passthrough + `PROVIDER`-fallback cases).
- `test_events.py`: `_TERMINAL_ERROR_KINDS` replaced by an import from
  the shared module.

Scope kept to the four shipped adapters; `MyServiceAdapter` /
`StubAdapter` test doubles keep their inline `map_provider_error` dicts
(test-local, no `error_kinds` ClassVar — refactoring the reference
adapter is out of scope), and the anticaptcha/capmonster/capsolver
`map_provider_error` spot-checks stay (they assert end-to-end behavior,
not a table re-declaration).

### Verification

`uv run ruff check .` / `ruff format --check .` / `mypy unicaptcha` /
`pyright` / `slotscheck unicaptcha` / `uv run pytest` — all pass
(494 passed, 7 integration deselected; +5 new guard tests).

### Spec/ADR amendments

None.

### Future-task notes

- The `myservice` reference adapter (and `StubAdapter`) still carry
  private code→kind dicts inline; folding them onto the shared tables
  would require giving them an `error_kinds`-style ClassVar first.
- Related deferred tasks remain open: "Async clock seam", release
  readiness, and the auto-mode feature (ADR-0077).