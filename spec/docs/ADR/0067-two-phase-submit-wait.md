# ADR-0067: Two-phase submit/wait with TaskTicket

**Status:** Accepted (amends ADR-0010, ADR-0018, ADR-0038, ADR-0045, ADR-0051; closes deferred item 10; notes deferred item 7; wait's poll-delay skip per the ADR-0030 amendment; amended by ADR-0075: TaskTicket gains an `instant_answer` field, wait fast-path for inline-answered submits; renamed 2026-08-24: `Result[T]` → `SolveResult[T]` → `TaskResult[T]`, `TaskStatus` → `TaskStatusResult`, `get_task_result` → `get_task_status` — task-centric vocabulary; amended 2026-08-24: `submit` takes `on_event=`, no `time=` — retry-bounded, not budget-bounded)
**Date:** 2026-08-23, amendment 2026-08-24

## Context

`solve()` is monolithic: submit and poll in one call. Batch workflows
(submit N tasks now, collect as they mature) have no honest path — they
must run N concurrent `solve()` calls, each holding its own budget.
The engine already separates the phases internally (the reason
webhooks were called additive, deferred item 7). Competitive analysis
(unicaps/anycaptcha) confirmed the workflow is real: their
`create_task` + `wait()` split is a used feature.

Design session settled five questions one by one (return type, method
placement, budgets, facade parity, vehicle).

## Decision

### Phase 1 — submit

```python
ticket = solver.submit(challenge, provider=None, retry=None, on_event=None)   # -> TaskTicket[SolutionOf[C]]
ticket = tc.submit(ImageChallenge(Path("t.png")))              # facade: implicit provider
```

- Provider routing identical to `solve()` (ADR-0064: kind-base
  dispatch with optional `provider=` / random; concrete classes
  direct).
- Submission itself is bounded by the retry policy (ADR-0011), not by
  `total_timeout` — `submit` takes `retry=` and `on_event=` but **no
  `time=`** (no total budget on a bare submit; amended 2026-08-24).

### TaskTicket

- Frozen dataclass, generic over the solution type: `task_ref:
  TaskRef`, `submitted_at: datetime` (UTC-aware). `T` binds via the
  challenge->solution link (ADR-0048) at submit time.
- **Not user-constructible** (enforcement at implementation, same
  spirit as solution bases): its value is provenance — a self-built
  ticket would lie about `T`. (Owner amendment 2026-08-26: enforced by
  **documentation and provenance**, not a runtime guard — Python cannot
  prevent construction of a concrete public dataclass, and ADR-0035's
  base-guard pattern does not apply to a concrete leaf.)
- Bridges to persistence via `.task_ref` (ADR-0045 unchanged:
  TaskRef remains the constructible identity object).

### Phase 2 — three methods, no unions

| Method | Accepts | Returns | On terminal failure |
|---|---|---|---|
| `wait(ticket, timeout=None)` | `TaskTicket[T]` | `TaskResult[T]` | **raises** (`NoSolutionError`, `ProviderError` on UNKNOWN per ADR-0058, `TaskTimeoutError`) |
| `wait_ref(ref, timeout=...)` | `TaskRef` | `TaskStatusResult` | **answers**; budget exhaustion returns PENDING `TaskStatusResult` |

`wait_ref` with `timeout=None` uses the generic fallback budget/cadence
(120 s budget, 5 s poll interval): no per-kind timing exists for a bare
`TaskRef` (per-kind defaults attach to challenges/tickets only).
| `get_task_status(ref)` | `TaskRef` | `TaskStatusResult` | answers — single-shot, unchanged (ADR-0050) |

- `wait` is an **operation** (solve-parity semantics); `wait_ref` and
  `get_task_status` are **queries** (ADR-0050 semantics). A single
  `wait` overloaded on argument type was rejected: its return type and
  error philosophy would depend on the argument — two methods wearing
  one name.
- All three live **on the solver** (both tiers); TaskTicket and
  TaskRef stay dumb frozen data (picklable, no engine
  back-reference). Handle methods (`ticket.wait()`) rejected: an
  engine reference inside frozen data breaks pickling and TaskRef's
  constructibility contract.
- Facade validation: `wait(ticket)` / `wait_ref(ref)` on a facade
  whose provider differs from the ticket/ref -> pre-flight `TypeError`
  naming both parties (ADR-0045 precedent).

### Budgets

- `wait(timeout=None)`: the clock **starts at the `wait()` call**; the
  budget covers polls + transient-failure tolerance (ADR-0011 poll
  rules). Default resolves through the None-merge chain (ADR-0043) to
  the per-kind `total_timeout` (ADR-0030: image 30 s, text 120 s,
  reCAPTCHA-class 120 s) — so `solve() = submit() + wait(default)`.
- Wall-clock anchoring at `submitted_at` (Option B) was rejected:
  fresh-budget-at-call is simpler to reason about, and providers do
  not bill by our clock.
- `wait_ref` shares the semantics (call-start clock); exhaustion
  answers PENDING, never raises.
- **Poll-delay skip** (ADR-0030 amendment): `wait(ticket)` applies
  the per-kind `poll_delay` only when the ticket is **fresh**
  (submitted less than one `poll_interval` ago); stale tickets poll
  immediately — an old task is likely already mature. `wait_ref` /
  `get_task_status` never apply a delay.
- `total_timeout` (ADR-0010) is thereby scoped to `solve()`; this
  closes deferred item 10 — the granular split exists, expressed as
  two calls rather than two config knobs.

### Facade parity

`submit` / `wait` / `wait_ref` on every `<Provider>Client` /
`Async<Provider>Client`, signatures identical to the universal tier
(provider implicit). `submit` is provider-agnostic in shape — no
per-kind method explosion; the challenge carries the kind.

### Behavioral pins

- **Events** (amends ADR-0018 invariant): `SUBMIT_ACCEPTED` fires at
  submit; `RESULT_RECEIVED` / `RESULT_FAILED` fire at wait's terminal
  state; tasks never waited are eventless forever (mirroring
  cancellation's eventlessness). Invariant reworded: "every *waited*
  solve ends in exactly one of `RESULT_RECEIVED` or `RESULT_FAILED`."
- **Abandoned registry** (amends ADR-0038): intentional deferral is
  NOT abandonment. Registry entries appear only when a `wait` is
  cancelled mid-loop or orphaned by close. Process death between
  submit and wait leaves no trace; the persisted `task_ref` is the
  remedy (same honesty as ambiguous failures, ADR-0011).
- **Billing caveat** documented at `submit`: a solved-but-uncollected
  task is billed by the provider; collection is the caller's job.
- `solve()` unchanged — the monolithic path remains the common case.

## Rationale

- The engine's internal phase split gets a public face at zero
  architectural cost; batch submission stops being N concurrent
  monolithic solves.
- The ticket/ref pair mirrors reality: fresh submissions know the
  kind (typed results); persisted identities cannot (honest
  `BaseSolution` answers, ADR-0056 reasoning).
- Three single-purpose methods beat one polymorphic `wait`:
  discoverable contracts, honest signatures, no union returns.

## Alternatives considered

- **Overloaded `wait(ticket | ref)`**: rejected; union return type +
  error semantics that depend on the argument.
- **`wait` accepting refs only** (no ticket): rejected; `T` unbindable
  (ADR-0056's TaskStatusResult problem again) on the primary path.
- **Handle methods (`ticket.wait()`)**: rejected; engine reference in
  frozen data.
- **Wall-clock deadline from `submitted_at`**: rejected; surprises
  late collectors, no operational gain.
- **`get_task_status(ref, timeout=...)` loop variant**: rejected;
  pollutes a settled single-shot method (ADR-0050) — hence separate
  `wait_ref`.
