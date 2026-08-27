# ADR-0003: Blocking sync + async-native architecture

**Status:** Accepted
**Date:** 2026-08-22 (amended 2026-08-23 to drop the pydantic dependency reference)

## Context

Anti-captcha solving is a long poll loop (submit, wait, fetch). The library
must serve both plain scripts (sync) and high-concurrency applications
(async). Two broad strategies exist: one async core with a sync wrapper
(e.g. background event loop thread, `asyncio.run` bridging), or two
implementations sharing pure logic.

An earlier proposal (async core + sync wrapper via a persistent event-loop
thread) was challenged during design: why should a sync method spawn or
attach to async machinery when it can simply block?

## Decision

Two peer implementations:

- **Async**: native asyncio. `await http` + `asyncio.sleep`; internal
  timeout via `asyncio.timeout()`; `CancelledError` propagates untouched
  (ADR-0016).
- **Sync**: plain blocking. Blocking httpx calls + sleep implemented on a
  `threading.Event` shutdown wait (ADR-0033); `KeyboardInterrupt`
  propagates naturally.

Shared between them: all models, validation, adapters (pure translation),
config resolution, event construction, logging. Only the I/O-and-sleep loops
are written twice, and they are thin: the solve flow's branching lives in
pure helpers.

No wrapper magic in either direction: no background event-loop threads, no
`run_coroutine_threadsafe`, no `asyncio.run` per call.

## Rationale

- The sync path stays trivially debuggable with zero async overhead, and
  works inside running loops (Jupyter) without special handling.
- The async path never pays thread-bridging costs or contortions.
- The genuinely duplicated code (the poll loop) is ~15 lines per side.
- httpx provides `Client`/`AsyncClient` with identical request semantics,
  making behavioral parity cheap.

## Alternatives considered

- **Async core + sync wrapper** (background-thread loop or `asyncio.run` per
  call): rejected after owner pushback; sync should just block. Wrappers add
  failure modes (loop-inside-loop, per-call loop overhead, thread lifecycle).
- **Sync only**: rejected; async concurrency is a primary use case.
- **Single algorithm with injected I/O primitives** (state machine yielding
  request/sleep steps interpreted by each side): rejected as over-engineering
  for a loop this small; revisited only if the flow grows complex.
