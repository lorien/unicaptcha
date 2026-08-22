# ADR-0023: README-only documentation for v1

**Status:** Accepted
**Date:** 2026-08-22

## Context

Documentation tooling (Sphinx, MkDocs with generated API reference) is a
maintenance surface. For an experimental pre-1.0 library the served
audience is early adopters reading GitHub/PyPI.

## Decision

End-user documentation for v1 is the **README only** (project root): what
the library is, provider/kind table, install, usage sketch, adapter-SDK
mention, experimental notice, MIT, repository URL. No doc generator, no
hosted docs site.

Internal design documentation lives in `spec/ref/` (this knowledge base),
hand-written markdown, no tooling.

Doc-site generation (MkDocs/Sphinx) is not deferred as a commitment — it
simply does not exist in the v1 plan; revisit after API stabilization.

## Rationale

- Owner decision: minimal surface while the API churns; generated
  reference docs of an unstable API age poorly.
- README doubles as the PyPI landing page.

## Alternatives considered

- **MkDocs + mkdocstrings from the start**: rejected for v1.
- **Sphinx**: rejected for v1.
