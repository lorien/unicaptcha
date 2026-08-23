# ADR-0065: Accept `Path` for challenge image bodies

**Status:** Accepted (amends ADR-0025)
**Date:** 2026-08-23

## Context

ADR-0025 settled image input as raw `bytes` only — rejecting base64
strings, file-like objects, and URLs. That rejected chaos was real,
but `Path` is different in kind: stdlib, concrete, zero ambiguity.
Post-ADR-0063 review of setup ceremony found `Path(...).read_bytes()`
to be the last boilerplate line in the minimal example. Same shape
as ADR-0063: convenience at the boundary, normalization inside.

## Decision

- `body: bytes | Path` on `ImageChallenge` (inherited by every
  provider image subclass).
- **Boundary normalization** in `__post_init__`: a `Path` is read
  (`read_bytes()`) and the field **always stores `bytes`** — snapshot
  semantics (later file changes don't matter, identical to the caller
  reading it); frozen/immutability guarantees unchanged.
- **Read failure** (missing file, permissions, ...) raises
  `InvalidChallengeError` chained `from` the original `OSError` — one
  exception family for caller mistakes (ADR-0041), standard chaining
  discipline.
- **`Path` only**: file-like objects (`BytesIO`, open handles) and
  `str` paths remain rejected — `BytesIO.getvalue()` /
  `Path(s)` are one call each, and the file-like slope is ADR-0025's
  original mess.
- Scope: image bodies only. `TextChallenge.text` is `str`; output
  surfaces (`raw`) are read-only and unaffected.

## Rationale

- Two-member union, both typed; nothing ambiguous enters.
- The stored representation stays plain `bytes`, so adapters, repr
  policies, and pickling see no change.
- Construction-time read is one small synchronous file read; failing
  fast with a chained, on-family error keeps the mistake at the
  construction line.

## Alternatives considered

- **`bytes` only** (status quo): superseded; ceremony without added
  safety, same argument as ADR-0063.
- **Accept file-like objects / `str` paths**: rejected; the exact
  ambiguity ADR-0025 exists to prevent.
- **Raw `OSError` propagation**: rejected; off-family, inconsistent
  with every other construction-time validation.
