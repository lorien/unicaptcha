# ADR-0078: Static documentation site (supersedes ADR-0023)

**Status:** Accepted
**Date:** 2026-09-04

## Context

ADR-0023 scoped end-user documentation to the README only for v1,
deliberately deferring doc-site generation "until API stabilization".
The public API has since stabilized in shape (four providers, nine kinds,
universal client + facades, typed result/config/error/event surface), and
the README can no longer carry the full reference.

## Decision

End-user documentation is a **standalone static site** built with
**MkDocs + Material for MkDocs + mkdocstrings**:

- Source lives in the repository root `docs/` (markdown guides + an
  auto-generated API Reference).
- The API Reference is generated from the package's own docstrings via
  `::: unicaptcha.<module>` directives (`mkdocstrings`, Python handler);
  it covers the full public surface.
- `spec/docs/*` remains the **internal** design record (ADR-0023 context)
  and is **never linked or imported** from the public docs. Public pages
  are self-contained; where they restate facts from the design record
  (provider/kind tables, config semantics, error kinds), they do so in
  their own words.
- The README stays as the PyPI/GitHub landing page and points at the
  docs site.
- Build only for now: `uv run mkdocs build` produces `site/`; no CI
  deployment or hosted docs site yet.

## Rationale

- Markdown-native fits the repository's prose workflow; Material provides
  search, navigation, and a modern look with near-zero configuration.
- mkdocstrings renders the existing strict-typed docstrings, so the
  reference cannot drift from the source.
- Keeping the end-user site separate from the internal design record lets
  each speak to its own audience without cross-contamination.

## Alternatives considered

- **README only (status quo)**: rejected — insufficient for the full
  public surface.
- **Sphinx + autodoc + Furo**: viable, but RST/MyST-centric and heavier
  config; MkDocs matches the repo's markdown flow and toolchain.
- **Hosting the design record publicly**: rejected; `spec/docs/*` is the
  internal knowledge base, not end-user documentation.