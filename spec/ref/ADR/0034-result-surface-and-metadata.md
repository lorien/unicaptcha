# ADR-0034: Result surface and metadata

**Status:** Accepted
**Date:** 2026-08-23

## Context

Two loose ends from the result design: the `raw` field's type (parsed JSON
vs bytes — errors had settled on bytes) and the exact metadata field set.

## Decision

- **`raw: bytes`** — the untouched HTTP response body. One convention
  everywhere: "raw means the verbatim wire payload". Ergonomic access is
  what the typed fields are for.
- Metadata set: `provider: str` (adapter provider string; also the aux-op routing
  key), `created_at: datetime` (task submission time, UTC, timezone-aware),
  `elapsed: timedelta` (submission -> ready). No poll-count (internal
  noise; already in events), no captcha-type field (derivable from the
  solution type).
- **repr policy**: bytes fields render as `<N bytes>` stubs; solution
  tokens/text render truncated `***abcd` (last 4 chars); API keys fully
  masked; `str` mirrors `repr`; custom `__repr__` on affected frozen
  dataclasses; internal `_internal` objects keep default reprs.

## Rationale

- bytes-for-raw: symmetry with `error.raw_response`; no second `raw`
  convention to remember; parsed-JSON ergonomics duplicate typed fields.
- The metadata triple covers cost monitoring (provider), audit
  (created_at), and latency SLOs (elapsed) without speculative extras.
- Truncation policy keeps consoles/logs readable and secrets-adjacent
  values safe while retaining correlatability.

## Alternatives considered

- **`raw: Mapping[str, Any]`**: rejected; breaks uniformity with errors,
  loses wire fidelity.
- **Poll count / captcha type in metadata**: rejected; derivable or
  event-sourced.
- **Full token display in repr**: rejected; tokens are secrets-adjacent
  single-use artifacts.
