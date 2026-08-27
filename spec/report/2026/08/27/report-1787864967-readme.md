## Report on task: README: finalized usage

### Task (archived from plan.md)

```
## README: finalized usage

Status: done

Rewrite README.md to match the implemented API:

- Fix the stale import path (`unicaptcha.provider.…`, not
  `unicaptcha.providers.…`), add Turnstile to the nine-kind list, and
  replace the "usage sketch" with finalized usage: universal
  `Solver`/`AsyncSolver`, kind-base routing, provider facades, two-phase
  batch, aux operations, errors.
- Add `tests/test_readme.py` doc-consistency checks (all nine kinds
  present; correct singular `provider` import path).

References: ADR-0023, ADR-0064, ADR-0067, ADR-0072.
```

### Done

- Rewrote `README.md` to match the shipped API:
  - Corrected the import path (`unicaptcha.provider.twocaptcha`, not the
    stale plural `unicaptcha.providers.…`).
  - Replaced the bullets kind list with a nine-kind table (added
    Cloudflare Turnstile), pairing each kind with its challenge/solution
    base classes; noted that kind coverage varies by provider.
  - Replaced the "Usage sketch" (which said the API was still being
    finalized) with finalized usage: universal `Solver`/`AsyncSolver`
    example, kind-base vs concrete challenges + `provider=` pinning vs
    uniform random routing (ADR-0064), provider facades with sync and
    async examples (ADR-0061/0051), two-phase `submit()`/`wait()`/
    `wait_ref()` (ADR-0067), aux operations, the error hierarchy pointer,
    and the `on_event=` events surface.
  - Kept the experimental notice, supported-services table, base-URL
    mirrors (RuCaptcha), install, referral/funding note (ADR-0072),
    custom-provider SDK section, and license.
- Added `tests/test_readme.py` with two prose-only doc-consistency guards:
  the README's kind section names all nine v1 kinds, and the README uses
  the singular `provider` import path (never the stale plural).
- Verification: `uv run pytest` (452 passed, incl. the new test), `uv run
  ruff check .`, `uv run ruff format --check .`, `uv run mypy unicaptcha`,
  `uv run pyright unicaptcha`, `uv run slotscheck unicaptcha` — all clean.

### Spec/ADR amendments

- None needed: the README documents the API as implemented; no ADR or spec
  doc changes were required.

### Future-task notes

- The two sibling sub-tasks split out of the original "README + CHANGELOG"
  record remain open in `plan.md`: "CHANGELOG: v1 Unreleased summary" and
  "Release-consistency CI guards".

### Tooling/process

- [open] README code snippets are prose-reviewed against the signatures
  but never executed (ADR-0023 keeps v1 docs tooling-free). If snippet
  drift ever becomes a problem, a doctest/`ast.parse` pass over the code
  blocks could be added; deferred per ADR-0023.