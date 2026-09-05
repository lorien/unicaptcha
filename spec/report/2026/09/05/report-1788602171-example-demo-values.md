## Report on task: Example demo values — geetest_v3 dynamic challenge; funcaptcha annotation

### Task (archived from plan.md)

Status: done

Live smoke (2026-08-28): geetest_v3 examples fail with `NoSolutionError`
— the static demo `challenge` is stale by design (one-time value). Fetch
a fresh challenge from the 2captcha demo page per run (the vendor SDK
example's pattern: GET the page, `split(';')[0]`) in sync/async examples.
FunCaptcha's public demo blob is not worker-solvable; keep those examples
illustrative with an explicit docstring/README note (`NoSolutionError`
expected).

### Resolution

The plan's prescribed fetch was investigated and **rejected**: the
2captcha GeeTest demo page is now a React SPA whose raw HTML carries no
`initGeetest({gt, challenge})` call and no bare challenge literal — only
how-to text. The vendor `split(';')[0]` pattern would return a fragment
of the page's embedded JSON, not a valid challenge; `unicaptcha.detect`
on that HTML finds nothing. An env-var flow
(`UNICAPTCHA_GEETEST_V3_CHALLENGE`) was also considered and rejected by
the owner as contrived.

Final approach — **pure-illustrative** annotation for both kinds (owner
decision):

- `examples/{sync,async}/geetest_v3.py`: docstring notes the demo
  `challenge` is single-use by design and a live solve is expected to
  end in `NoSolutionError` (obtain a fresh challenge from the target
  page to solve for real); the stale inline "fetch a fresh one" comment
  corrected.
- `examples/{sync,async}/funcaptcha.py`: docstring notes the public
  Arkose demo blob is not worker-solvable; `NoSolutionError` expected.
- `examples/README.md` and `docs/guides/examples.md`: an
  "Illustrative examples" note covering both `geetest_v3.py` and
  `funcaptcha.py`.
- CHANGELOG `[Unreleased]` Added entry documenting the clarification.

No behavior change: the examples still run against the mocked transport
in `tests/test_examples.py` unchanged (expected outputs `challenge:` /
`token:`).

### Verification

`uv run ./scripts/check.sh` — ruff, mypy, pyright, slotscheck, pytest:
all pass (547 passed, 7 integration deselected). `uv run mkdocs build`
clean.

### Spec/ADR amendments

None.

### Future-task notes

- If a server-rendered public GeeTest v3 demo becomes available again,
  revisit making the example fetch a live challenge.