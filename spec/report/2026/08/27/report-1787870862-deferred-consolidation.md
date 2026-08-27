## Report on task: consolidate deferred.md into plan.md

### Done

- Deleted `spec/docs/deferred.md`; `plan.md` is now the single home of all
  open/parked work.
- Migrated the 17 open deferred items into `spec/docs/plan.md` as `## {title}`
  records (`Status: new`) at the bottom of the list: PyPI publishing,
  `examples/`, provider selection/failover policy, client-side rate limiting,
  API-key rotation, webhook solve mode, hierarchical logger names,
  `unicaptcha.testing`, capability introspection, usage statistics, deferred
  kinds, deferred providers, image classification tasks, template automation
  tasks, statistics endpoints, CI coverage gating, provider-fidelity
  verification method. Bodies condensed from the old `deferred.md` notes.
- The 5 closed deferred items (2, 10, 15, 19, 20) were dropped: their
  resolutions are already recorded in the ADRs that closed them.
- Added `## Observations backlog review` (Status: new) as the bottom record:
  review the `[open]`/`[needs-decision]` markers across `spec/report/` plus
  the recurring refactor/tooling themes, and turn each into a real `plan.md`
  task or remove it.
- Updated living docs that linked `deferred.md`:
  - `spec/docs/index.md`: removed the `deferred.md` documents-table row
    (plan.md row now says "Open tasks and parked work (includes formerly
    deferred items)"); reworded the four ADR-table notes that said
    "closes deferred 15/19/10/2" to describe what each ADR settles.
  - `spec/docs/goals.md`: replaced the `[deferred.md](deferred.md)` link
    with a pointer to `plan.md`.
  - `spec/docs/architecture.md`: reworded the two "deferred item 2"
    pointers (the field-surface heading and the worker-context note).
- ADR files left untouched as historical records (their "deferred item N" /
  "deferred.md" mentions remain accurate history per the established
  convention).
- Verification: `uv run pytest` (452 passed), `uv run ruff check .`,
  `uv run ruff format --check .`, `uv run mypy unicaptcha`,
  `uv run pyright unicaptcha`, `uv run slotscheck unicaptcha` — all clean.
  `rg "deferred.md" spec/docs/` now matches only the ADR files.

### Spec/ADR amendments

- No ADR edits; the consolidation is a docs-organization change only.

### Future-task notes

- `plan.md` now holds 19 records: the release-consistency CI guard (topmost
  `new`), 17 formerly-deferred items, and the observations-backlog review
  (bottom). The observations review will likely prune/merge several of the
  migrated records as it triages them.
- ADR cross-references to "deferred item N" are now historical pointers to a
  deleted file; living docs no longer rely on the numbering.

### Tooling/process

- [acted] Single-list rule recorded by deletion: there is one home for open
  work, `spec/docs/plan.md`; `deferred.md` no longer exists. Living docs
  (`goals.md`, `index.md`, `architecture.md`) point at `plan.md` instead.
- [open] The historical ADR references to "deferred item N" have no living
  map; if precise provenance is ever needed, `git log`/`git blame` on
  `deferred.md`'s deleted history recovers the old numbering.