## Report on task: Client usage statistics

### Task (archived from plan.md)

Status: done

Cumulative solved/failed counters, Decimal cost totals, per-provider
breakdown; prefer an `on_event`-fed collector over client state.

### Done

- New public `unicaptcha/stats.py`, exported from the root:
  - `StatsCollector` — a synchronous `on_event` handler (works as
    `on_event=` on `Solver`, `AsyncSolver`, and the facades; the async
    handler accepts a sync callable). Tallying is guarded by a
    `threading.Lock` for concurrent solves (ADR-0027 thread-safe client).
  - `UsageStats` (frozen) — `solved`, `failed`, `elapsed: timedelta`,
    `per_provider: Mapping[str, ProviderUsage]`, `attempts` property.
  - `ProviderUsage` (frozen) — `provider`, `solved`, `failed`,
    `elapsed`, `attempts` property.
  - `snapshot() -> UsageStats` (immutable copy) and `reset()`.
  - Classification from terminal events (one per solve invocation):
    `RESULT_RECEIVED` → solved; `PRE_FLIGHT_FAILED` / `SUBMIT_FAILED` /
    `RESULT_FAILED` → failed; non-terminal kinds ignored.
- **Cost totals deliberately excluded** per owner decision: providers may
  bill in different currencies (ADR-0040's unacted verification note;
  RuCaptcha is RUB-scoped), so summing `Decimal` costs would mix
  currencies. Deferred to the new plan record "Currency-aware costs".
- Tests: `tests/test_stats.py` (8 tests) — terminal/non-terminal
  classification, per-provider breakdown, elapsed summation, immutable
  snapshot, reset, sync/async/auto_solve end-to-end over respx.
- Docs: `docs/guides/events.md` "Usage statistics" section,
  `docs/api/stats.md` + nav entry, CHANGELOG `[Unreleased]` Added entry.

### Verification

`uv run ./scripts/check.sh` — ruff, mypy, pyright, slotscheck, pytest:
all pass. `uv run mkdocs build` clean.

### Spec/ADR amendments

- `spec/docs/plan.md`: the "Client usage statistics" record archived
  here; new "Currency-aware costs" record added (deferred), which will
  resolve ADR-0040's currency pin and extend the stats to count cost.

### Future-task notes

- "Currency-aware costs": settle provider cost/balance currency
  (ADR-0040 verification note), then add `cost` to `TaskEvent`
  (`RESULT_RECEIVED` only — the engine already holds `parsed.cost` at
  the emit site) and total costs per provider + cumulative in
  `UsageStats`.