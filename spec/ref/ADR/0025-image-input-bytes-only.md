# ADR-0025: Image input as bytes only

**Status:** Accepted
**Date:** 2026-08-23

## Context

Image challenges need a body. Candidate input types: raw `bytes`, base64
string, `Path` to a local file, or URL (some providers fetch URLs
themselves). The choice defines the most-used call surface.

## Decision

Image challenge `body` accepts **`bytes` only**. The library base64-encodes
internally (all three APIs expect base64). No file reading, no URL
fetching, no pre-encoded string acceptance.

Text challenges take `str` (the question text) plus provider-specific
fields; no input-type ambiguity exists there.

## Rationale

- Owner decision; single canonical type keeps validation honest (empty
  body, oversized payload checks on real data) and signatures simple.
- Callers read files (`Path.read_bytes()`) or fetch URLs in their own
  code with their own error handling — the library does not hide I/O.
- Providers differ in URL support (2Captcha can fetch; others cannot);
  a `bytes`-only surface avoids per-provider divergence in a universal
  field position.

## Alternatives considered

- **bytes | base64 str**: rejected; ambiguity (is this base64 or raw?) is
  a bug factory.
- **+ `Path`**: rejected; hidden file I/O in constructors.
- **+ URL with provider-side fetching**: rejected; per-provider support
  differences; hidden network I/O.
