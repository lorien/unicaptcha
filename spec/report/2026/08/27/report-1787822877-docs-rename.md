## Report on task: rename spec/ref to spec/docs

### Spec/ADR amendments

- [acted] Renamed the knowledge base directory `spec/ref/` → `spec/docs/`
  (`git mv`, history preserved; ADR/ subdir and all 10 docs moved).
- [acted] Updated all 11 `spec/ref` references across 9 files to
  `spec/docs`: CHANGELOG.md (1), README.md (2), spec/skills/{shell,task,
  work}.md (4), report-1787783615-providers-reference.md (2),
  ADR/0074 (1), ADR/0023 (1).
- [acted] Verified no `ref/`-prefixed, `../`, or absolute links inside the
  moved docs (all internal links are directory-relative, so they survive
  the rename); `rg 'spec/ref'` returns nothing repo-wide.

### Tooling/process

- [open] The `git mv` rename preserved history, but the earlier commit
  `59b8f8e` and the skills files (`spec/skills/*.md`) hardcode the
  `spec/docs/` path in prose; if the knowledge base moves again, prefer
  relative links (or a single source of truth) so the same sweep isn't
  needed.