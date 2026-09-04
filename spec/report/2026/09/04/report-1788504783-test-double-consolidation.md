## Report on task: Test-double consolidation (`_fake`/ScriptedAdapter → `_myservice`)

### Task (archived from plan.md)

Status: done

FakeAdapter + ScriptedAdapter + the reference MyServiceAdapter coexist;
consolidating onto `tests/_myservice.py` would remove triple duplication
of a provider double.

### Done

The plan's framing ("triple duplication", "consolidate onto
`_myservice.py`") did not survive contact with the code. Investigation
found **four** doubles serving distinct roles:

- `_fake.FakeAdapter` — minimal myservice stub for SDK-contract tests
  (base-default report behavior, key wrapping, base_url, referral, repr).
- `test_engine.ScriptedAdapter` — minimal myservice stub for engine-core
  tests (reports on, real parse logic, `FakeSolution`).
- `test_client.ScriptedAdapter` — a *different* "scripted" family
  (payload introspection of sitekey/proxy/task_ref; Alpha/Beta/Upcast
  subclasses) used for Solver routing tests.
- `_myservice.MyServiceAdapter` — the full ADR-0046 reference adapter
  (public-only imports CI-enforced); folding stubs into it would degrade
  its documentation role and force large rewrites for no behavioral gain.

`_fake.FakeSolution` (6 files) and `_fake.FakeClock` (timing suite) are
separate concerns and stay.

Scope executed:

- Merged the two minimal myservice stubs into one shared
  `ScriptedAdapter` in `tests/_fake.py` (verbatim from the engine
  version); deleted `FakeAdapter`.
- `test_engine.py` imports the shared adapter and dropped its 70-line
  inline class; removed the now-unused `error_from_kind` /
  `BaseAdapter` / `BaseChallenge` / `ErrorKind` / `ParsedTask` /
  `SubmitAccepted` imports.
- `test_adapter_sdk.py` switched `FakeAdapter` → shared `ScriptedAdapter`
  everywhere except `TestReportDefaults`, which is the one place that
  asserts *base-default* report behavior; it now uses a local
  `MinimalAdapter` (base report defaults off).
- Renamed `test_client.py`'s distinct `ScriptedAdapter` → `ProbeAdapter`
  to remove the same-name-across-files collision; Alpha/Beta/Upcast
  subclasses unchanged.

### Verification

`uv run ruff check .` / `ruff format --check .` / `mypy unicaptcha` /
`pyright` / `slotscheck unicaptcha` / `uv run pytest` — all pass
(489 passed, 7 integration deselected, identical to before).

### Spec/ADR amendments

None. The plan record's literal target (`_myservice.py`) was not pursued;
the archived record reflects the real scope.

### Future-task notes

- The rename-session future-note about switching `MyServiceAdapter` from
  `BaseAdapter` to `AntiCaptchaCompatAdapterBase` remains open — a real
  tradeoff (it currently documents the raw `BaseAdapter` contract path),
  not a mechanical step.
- The related "Shared ErrorKind mapping table" plan record remains open;
  the shared `ScriptedAdapter.error_kinds`-style mapping could seed it.