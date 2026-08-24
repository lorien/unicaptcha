# ADR-0075: Submit-phase ready fast-path with SubmitAccepted

**Status:** Accepted (amends ADR-0053, ADR-0067; formalizes `ParsedTask` from ADR-0058)
**Date:** 2026-08-24

## Context

Capsolver's `createTask` answers `status: "ready"` with an inline solution
for instant tasks (ImageToText, classification) — observed in the official
SDK during the 2026-08-24 competitor analysis. The current adapter contract,
`parse_submit_response(raw) -> int`, cannot express that outcome:
the engine would discard the provider's answer and pay `poll_delay` plus
one `getTaskResult` round trip before learning what it already knew.

Only Capsolver instant tasks are known to behave this way; polled token
kinds (reCAPTCHA, hCaptcha, Turnstile, GeeTest, ...) are unaffected, and
the other three providers' adapters never return a ready parse.

Design review of the first sketch (`int | ParsedTask` union) found two
flaws, fixed here: the union loses `task_id` on the ready arm (breaking
`report_*_result` and `get_task_result` addressing), and an engine-side
cache keyed by TaskRef (to bridge separate `submit()`/`wait()` calls) is
hidden mutable state — the ADR-0060 anti-pattern.

## Decision

### Typed contract

```python
@dataclass(frozen=True, slots=True)
class ParsedTask:                      # public adapter-SDK vocabulary
    state: TaskState                   # PENDING | READY | UNSOLVABLE | UNKNOWN
    solution: BaseSolution | None      # provider subclass; populated only when READY
    cost: Decimal | None               # presence-check (ADR-0034)
    raw: bytes                         # verbatim body
    detail: str | None = None          # provider message; feeds ProviderError (ADR-0058)


@dataclass(frozen=True, slots=True)
class SubmitAccepted:
    task_id: int                       # ALWAYS present; missing = malformed response (ADR-0040)
    ready: ParsedTask | None = None    # set iff createTask answered inline
```

`BaseAdapter.parse_submit_response(raw: bytes) -> SubmitAccepted`
(amends the ADR-0053 member table). `ParsedTask` — previously pinned only
by role (ADR-0058, architecture.md §9) — is hereby formalized as this
typed surface and exported as public vocabulary (`unicaptcha.types`,
root re-exports), alongside `SubmitAccepted`; the adapter SDK is public
(ADR-0041), so its return types must be.

### The ticket carries the answer — pure data, no engine state

```python
@dataclass(frozen=True)
class TaskTicket[T]:
    task_ref: TaskRef
    submitted_at: datetime             # UTC-aware
    ready: ParsedTask | None = None    # ADR-0075
```

ADR-0067 rejected handle **methods** because an engine reference inside
frozen data breaks pickling; a pure-data optional field violates nothing.
Tickets remain dumb, picklable, user-inspectable.

### Behavior

- `wait(ticket)`: `ticket.ready is not None` → return `Result[T]`
  immediately — no poll, no `poll_delay` (the fresh-ticket delay question
  is moot; there is no poll). Otherwise the unchanged poll path.
- `wait_ref(ref)` / `get_task_result(ref)`: **unchanged**. They take
  `TaskRef`, never see the field, and poll the provider — which returns
  READY with solution and cost on the first request, since the task is
  genuinely finished there. The provider is the source of truth; the
  ticket is a shortcut. One truth, two presentations (ADR-0050 ethos).
- `solve()`: consumes `SubmitAccepted` as a local variable; short-circuits
  submit → `Result[T]` without an intermediate ticket when the caller
  hasn't split the phases.
- Events: `submitted` then `solved`; no poll phase (ADR-0067 invariant
  intact). Cost from `ready.cost`; `None` unless the submit response
  reported one (ADR-0034 presence-check).
- Persisted/reconstructed `TaskRef`s take the poll path — already correct
  under ADR-0030's stale-ticket rule.

### Obligations

- `ParsedTask.__repr__` follows the repr policy (tokens `***abcd`, bytes
  `<N bytes>` stubs — ADR-0034) because it rides public objects.
- Adapters that never see inline-ready responses return
  `SubmitAccepted(task_id=..., ready=None)` — zero impact on the other
  three providers and third-party adapters.

## Rationale

- Provider fidelity (goal 2): the provider already answered; reading its
  answer off the ticket is cheaper and more honest than a confirming
  round trip.
- `task_id` stays guaranteed on both arms (ADR-0040 required-field rule),
  so aux-op addressing (`report_bad_result`, `get_task_result`) and the
  abandoned-registry story are untouched.
- No hidden state: everything the fast path needs travels on the ticket
  as data; the engine holds nothing between calls.

## Alternatives considered

- **`int | ParsedTask` union**: rejected in review; loses `task_id` on
  the ready arm, breaking report/result addressing.
- **Engine-side cache keyed by TaskRef**: rejected; hidden mutable state
  with lifecycle questions (eviction, abandoned waits, memory) — the
  ADR-0060 anti-pattern relived.
- **Fast path inside `solve()` only; split-phase `submit()`/`wait()`
  always poll**: rejected; two-phase users pay `poll_delay` + one round
  trip for tasks the provider already answered.
- **Drop the feature; treat inline solutions as malformed**: rejected;
  the response is well-formed provider behavior, and discarding it wastes
  time and money on Capsolver instant tasks.
