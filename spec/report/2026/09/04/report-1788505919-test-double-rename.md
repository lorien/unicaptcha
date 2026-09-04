## Report on task: Rename test doubles (follow-up to test-double consolidation)

Ad-hoc follow-up to the test-double consolidation session: the chosen
names `ScriptedAdapter` / `ProbeAdapter` were weak, so they were renamed
on owner feedback.

### Done

- `ScriptedAdapter` → `StubAdapter` (`tests/_fake.py` class; imports and
  ~30 annotations in `test_engine.py`; ~12 constructor uses plus the
  `repr` assertion in `test_adapter_sdk.py`).
- `ProbeAdapter` → `EchoAdapter` (`test_client.py` class, its
  `AlphaAdapter` / `BetaAdapter` / `UpcastAdapter` subclasses, and ~20
  references).
- `ruff format` applied after the shorter names made several previously
  multi-line signatures fit on one line.

### Verification

`uv run ruff check .` / `ruff format --check .` / `mypy unicaptcha` /
`pyright` / `slotscheck unicaptcha` / `uv run pytest` — all pass
(489 passed, 7 integration deselected). No behavior change.

### Spec/ADR amendments

None.

### Future-task notes

None.