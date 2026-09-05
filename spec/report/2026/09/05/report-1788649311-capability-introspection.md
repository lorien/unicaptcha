## Report on task: Capability introspection API

### Task (archived from plan.md)

Status: done

`client.supports(...)` / `providers_supporting(...)` and challenge-kind
tags. v1: probe by calling, catch exceptions.

### Done

- New public `unicaptcha/challenge/tags.py`: `KIND_TAGS` /
  `TAG_KINDS` (MappingProxyType, single source of truth) covering all
  nine kind bases → stable tag strings, exported from
  `unicaptcha.challenge` and the package root. `KIND_TAGS` uses the
  detect-established tags for the seven HTML-detectable kinds
  (`recaptcha-v2`, ...) plus `image` / `text`.
- `unicaptcha/detect.py` and `unicaptcha/_internal/_html.py` refactored
  to source their kind tags from the registry (`TAG_KINDS` for lookups,
  `KIND_TAGS` for signal tags) instead of duplicated inline literals —
  no more drifting second source of truth.
- `Solver` / `AsyncSolver` gain three synchronous, registry-only methods
  (no I/O; work even after `close()`):
  - `supports(kind) -> bool` — kind-base class or tag string; unknown
    kinds raise `TypeError`; valid-but-unsupported returns `False`.
  - `providers_supporting(kind) -> tuple[str, ...]` — provider names in
    registration order; `()` when none.
  - `supported_kinds() -> tuple[str, ...]` — tags covered by at least one
    registered adapter, in `KIND_TAGS` definition order.
  - Built on the existing internal `routing.supports_kind`.
- Tests: `tests/test_introspection.py` — tag registry round-trip and
  completeness, class/tag equivalence, unsupported-never-raises, unknown
  kinds → `TypeError`, registration order, `supported_kinds` ordering,
  works-after-close, async mirror, and a real-provider sanity check
  (`TwoCaptchaAdapter` covers all nine kinds). Existing detect/auto-solve
  tests cover the refactor.
- Docs: `docs/guides/universal-client.md` "Capability introspection"
  section; CHANGELOG `[Unreleased]` Added entry.

### Verification

`uv run ./scripts/check.sh` — ruff, mypy, pyright, slotscheck, pytest:
all pass (558 passed, 7 integration deselected). `uv run mkdocs build`
clean.

### Spec/ADR amendments

None required: the API is an additive client surface (ADR-0005); kind
tags are a new public mapping consistent with ADR-0048/0064/0070.

### Future-task notes

- The nine `KIND_TAGS` entries are the natural input for the deferred
  "Universal `solve()` kind overloads" task.
- `provider=` pinning on `supports()` was deliberately skipped for v1;
  callers can inspect `providers_supporting(kind)` membership.