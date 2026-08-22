# ADR-0038: Abandoned-task registry

**Status:** Accepted (amended: bounded with eviction warning and configurable cap; survives close)
**Date:** 2026-08-23

## Context

Cancellation (ADR-0016) and mid-solve client close (ADR-0033) orphan tasks
that may already be billed. Callers need the ids to reclaim answers.
Unbounded accumulation is a memory leak for long-running aggressive-cancelling
workers.

## Decision

- **Type**: registry entries are `TaskRef`s (public type, ADR-0045) with
  abandoned-at metadata available from the registry view. Routing info
  travels with the id.
- **Storage**: thread-safe append-only; `abandoned_tasks()` returns a
  snapshot `tuple`, never a live list.
- **Bounded**: default cap 1000 entries; when full, oldest entries are
  evicted with one WARNING log per eviction; cap configurable client-side
  (`abandoned_registry_limit`); `None` disables the bound for
  strict-losslessness use cases that accept the memory contract.
- **Entry lifecycle**: entries are added at submission time and removed
  when the solve delivers successfully; after abandonment they are removed
  only when a later `get_task_result` on that id reaches a terminal state
  (READY / UNSOLVABLE / UNKNOWN).
- **Registry survives close** (supersedes an earlier "cleared on close" --
  clearing would erase exactly the tasks close-orphaning creates).
  `abandoned_tasks()` remains readable on a closed client.
- **No automatic reclaim**: the caller drives `get_task_result`
  explicitly.
- Sync and async clients each carry their own registry (separate
  instances).
- Registry mutations are synchronous (no awaits) — safe during
  cancellation unwinding.

## Rationale

- Best-effort hints need honest bounds: ~200 bytes per entry, cap 1000 is
  invisible; unbounded-by-default would be a slow leak.
- Eviction with WARNING turns silent loss into a visible signal.
- Surviving close makes close-then-reclaim a supported workflow.

## Alternatives considered

- **Unbounded list**: rejected as memory leak; superseded by cap.
- **Cleared on close**: superseded; contradicts the close-semantics
  design.
- **Automatic reclaim loop in background**: rejected; hidden network
  activity, lifecycle complexity, policy creep.
