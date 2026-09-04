## Report on task: README snippet verification

### Task (archived from plan.md)

Status: done

README snippets are prose-reviewed only (ADR-0023). Options: execute
snippets with mocked transport or compile-check the fenced blocks (the
examples/ dir already gets compile checks via `tests/test_examples.py`).

### Done

Scope expanded from the README to the whole end-user documentation
(`README.md` + `docs/**/*.md`), now that the standalone docs site exists
(ADR-0078).

- New `tests/test_doc_snippets.py`:
  - `test_snippets_compile` — every ```python fence must `compile()`.
    Top-level `async with` / `await` fragments (legitimate in the docs,
    invalid at module scope) are retried wrapped in an `async def`.
  - `test_snippet_imports_resolve` — AST-walks each block's imports and
    verifies `unicaptcha` modules import and `from unicaptcha import X`
    names exist against the shipped package (drift guard against renamed /
    moved public API names — a compile-only check would miss, e.g., a
    snippet still using the old `JsonAdapterBase`).
  - Guards assert at least one fence exists (no silent no-op if docs are
    ever refactored to remove all fences).
- Fixed the one genuinely broken snippet found by the check:
  `docs/guides/errors.md` "Raw provider bodies" was a dangling `except`
  fragment; now a complete `try`/`except` example.
- The universal-client async fragment needed no doc change — the checker
  handles top-level async.

The checks run automatically in CI on every push/PR (the existing `test`
job's `uv run pytest`) and locally via `uv run pytest`.

### Verification

`uv run pytest tests/test_doc_snippets.py` — 2 passed. Full suite:
497 passed, 7 integration deselected. `uv run mkdocs build` clean;
`ruff check` / `format --check` clean.

### Spec/ADR amendments

None.

### Future-task notes

- Snippets are now guarded on syntax + unicaptcha imports, but not
  **executed** (they use placeholder keys/paths and would need a mocked
  transport). The examples/ dir already has the execution-level pattern
  (`tests/test_examples.py`, respx-mocked) if doc snippets ever need it.
- Shell/untagged fences (install commands, env vars) are not checked; a
  future shell-lint could cover them.