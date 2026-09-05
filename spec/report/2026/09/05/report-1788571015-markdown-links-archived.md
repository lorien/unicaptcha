## Report on task: Markdown link checker in CI (archived)

### Task (archived from plan.md)

Status: done

A README/docs link checker job; cheap, but decide scope (README only vs
spec/docs too) and whether broken-link tolerance is needed for external
URLs.

### Outcome

Already implemented — commit `2c31a47` (2026-09-04) added
`tests/test_markdown_links.py`: it walks `README.md`, `docs/`, and
`spec/docs/` and asserts every local relative link resolves to a real
file; external URLs and bare anchors are skipped, so the check is
deterministic and offline. It runs inside the pytest suite on every
push/PR, and since the check-set unification (commit `fad4070`) it runs
through `scripts/check.sh` → CI exactly as the local workflow.

All three open scope questions the record raised are settled by that
implementation:
- Scope: `README.md` + `docs/` + `spec/docs/` (all three, not README only).
- External URLs: skipped (no broken-link tolerance needed).
- CI placement: part of the pytest suite, no separate job.

### Verification

`uv run pytest tests/test_markdown_links.py` passes; no code change made
in this session.

### Spec/ADR amendments

None.

### Future-task notes

- The related open record "Report commit-hash traceability" remains
  undecided and is unaffected.