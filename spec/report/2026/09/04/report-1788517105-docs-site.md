## Report on task: Standalone end-user documentation site

Ad-hoc owner task (not a plan record): rich HTML end-user documentation
for the Python library, kept separate from the internal design record.

### Done

- **ADR-0078** ("Static documentation site") supersedes ADR-0023
  ("README-only documentation for v1"). End-user docs live in a
  standalone `docs/` tree; `spec/docs/*` remains the internal design
  record and is never linked/imported from public pages; README stays
  the PyPI/GitHub landing.
- **Deps**: `mkdocs`, `mkdocs-material`, `mkdocstrings[python]` added to
  the `dev` group (`uv.lock` is gitignored).
- **`mkdocs.yml`**: Material theme (light/dark), `search` +
  `mkdocstrings` (python handler, source-hidden, heading_level 3).
- **`docs/` guides** (self-contained prose, no `spec/docs/` links):
  index, getting-started, universal-client, facades, two-phase,
  configuration (with the real ADR-0030 per-kind timing table),
  proxy, errors (exception ↔ ErrorKind table), events, custom-providers
  (mentions `AntiCaptchaCompatAdapterBase`), examples (ported index).
- **`docs/api/` reference — full public surface** via
  `::: unicaptcha.<module>` directives: client, challenge, solution,
  types, errors, events, adapter, and the four provider packages.
- `.gitignore` now excludes `site/`.

### Verification

`uv run mkdocs build` builds clean (1.55 s); the built API-reference
pages render the symbols (`Solver`, `AntiCaptchaCompatAdapterBase`,
`TaskEventKind`, `TwoCaptchaClient` confirmed present). Existing suite
unaffected: `uv run pytest` 495 passed / 7 deselected; `ruff check`
clean. `rg spec/docs docs/` → only ADR-number provenance citations (e.g.
"(ADR-0030)"), no file links — standalone constraint holds.

### Spec/ADR amendments

- ADR-0078 (new) supersedes ADR-0023.

### Future-task notes

- **Deploy**: build-only for now; GitHub Pages deploy via CI is a later
  decision.
- **README**: still self-contained; can point at the docs site once a
  hosted URL exists.
- **Docs quality**: guide pages duplicate facts from `spec/docs/` by
  design; keep them in sync with the API reference (which is
  docstring-generated and cannot drift).
- The deferred "README snippet verification" plan item could be extended
  to the `docs/` guide code blocks (compile-check fenced Python).

### Tooling/process

- mkdocstrings renders existing docstrings with zero rewriting; the
  code's strict-typed docstrings were sufficient for the full reference.
- The Material "MkDocs 2.0" banner on build is informational only.