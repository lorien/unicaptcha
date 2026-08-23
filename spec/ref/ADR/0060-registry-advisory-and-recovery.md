# ADR-0060: Abandoned-task registry is per-client advisory; recovery workflow

**Status:** Accepted (amends ADR-0038; clarifies ADR-0033)
**Date:** 2026-08-23

## Context

ADR-0038 says entries are removed "when a later `get_task_result` on
that id reaches a terminal state" and markets "close-then-reclaim a
supported workflow". But registries are per-client (ADR-0038) and any
client able to reclaim after its own close must be a *new* client —
whose `get_task_result` cannot touch the closed client's registry.
The cleanup promise is unimplementable across the very workflow that
motivates it: reclaimed tasks stay listed in the dead client's
`abandoned_tasks()` forever (bounded, but misleading).

Second, the recovery workflow itself was only implicit — assembled
from ADR-0033 (close semantics), ADR-0038 (registry survives close),
ADR-0045 (TaskRef routing), ADR-0050 (query semantics) — never stated
in one place.

## Decision

- **The registry is per-client, best-effort, advisory.** It records
  what *this client instance* abandoned; it is a hint list, not a
  ledger of record. Stale entries in a closed client are intentional
  and harmless: the snapshot is bounded (cap, ADR-0038) and the truth
  about any entry is one `get_task_result` away.
- **Same-client cleanup** (the implementable part of ADR-0038's
  promise) is kept: a `get_task_result` reaching a terminal state
  removes the entry *from that same client's registry*.
- **Documented recovery workflow**:
  1. `abandoned_tasks()` on the closed (or live) client — snapshot of
     TaskRefs (survives close, ADR-0038);
  2. construct a new client (optionally) registering the same
     adapters; TaskRefs route by provider string (ADR-0045), no
     cross-instance coupling exists or is needed;
  3. `get_task_result(ref)` each entry — terminal states
     (READY/UNSOLVABLE/UNKNOWN) are answers (ADR-0050); READY yields
     solution + cost (ADR-0056);
  4. persist TaskRefs (provider + task_id) if reclamation must
     survive process restarts (ADR-0045: TaskRef is the durable
     representation).
- Billing caveat (ADR-0016) unchanged: abandoned tasks may still be
  billed; reclamation is the caller's remedy.

## Rationale

- Naming the registry advisory tells the truth about what per-client
  state can know; the alternative (shared/engine-level registry)
  would couple independent client lifecycles and break the clean
  ownership story of ADR-0033.
- The workflow section turns four ADRs' implications into copyable
  guidance — the primary justification the registry exists at all.

## Alternatives considered

- **Engine-level or adapter-level shared registry**: rejected; clients
  are independent (multiple clients per provider kind exist,
  ADR-0037 rationale); shared mutable state across lifecycles is the
  problem, not the fix.
- **Remove the cross-client cleanup claim only, keep wording
  ambiguous**: rejected; half-fixed contradictions resurface as bugs
  and bug reports.
- **Registry handoff on close (`new_client.adopt(old.abandoned_tasks())`)**:
  rejected; explicit but adds API surface for what TaskRef
  persistence + the documented workflow already achieve.
