# Plan

Open tasks. A task is a record with a `##` header (task name), a `Status:`
line, a `Priority:` line, the task body, and an optional `References:`
line.

Statuses:

- `new` — not started; ready to pick up.

Priorities:

- `Priority: N` right after the `Status:` line; default `0` for new
  records. Higher numeric value = more important.
- `Priority: -1` = deferred: the task is not auto-picked until its
  priority is raised.

A `done` task does not live here: when a task is finished, its record is
removed and archived into the report of the session that worked on it
(`spec/report/`). A task leaves plan.md only when its work is complete and
committed.

Selection picks the highest-priority `new` task; ties break by file order,
and `Priority: -1` (deferred) tasks are never auto-picked. The owner edits
`Priority:` values to reprioritize — no physical reordering needed.

Ad-hoc tasks requested directly by the user are not tracked here; their
reports live in `spec/report/`.

## Release-consistency CI guards

Status: new
Priority: -1

Add a `release-check` job to `.github/workflows/ci.yml` running on `v*`
tag pushes: tag == `unicaptcha/_version.py` version == matching
`## [{version}]` CHANGELOG section.

References: ADR-0021, ADR-0022.

## PyPI publishing / release automation

Status: new
Priority: -1

Whether a `v*` tag triggers automated publish, a TestPyPI dry-run, and
trusted publishing vs token. Deliberately postponed.

## Provider selection / failover policy

Status: new
Priority: -1

Kind-level uniform random selection exists (ADR-0064); still open:
*policy* routing — cheapest-first, failover, load balancing,
stickiness/weighting. A strategy wrapper could be a purely additive layer.

## Client-side rate limiting / concurrency caps

Status: new
Priority: -1

No `max_parallel_solves`, no request spacing in v1; callers manage
concurrency and the rate-limit retry with backoff is the safety net.

## API-key rotation

Status: new
Priority: -1

One key per provider instance in v1; rotation as a provider-level wrapper.

## Webhook/pingback solve mode

Status: new
Priority: -1

v1 is strictly poll-based; the submit/await split keeps a webhook mode
additive if ever added.

## Hierarchical logger names

Status: new
Priority: -1

v1 uses one flat `unicaptcha` logger; per-component names
(`unicaptcha.http`, `unicaptcha.provider.twocaptcha`, ...) if
per-component filtering is requested.

## unicaptcha.testing module

Status: new
Priority: -1

Fake clients / canned results / failure injection for downstream test
suites. Defer until the core API survives real usage.

## Capability introspection API

Status: new
Priority: -1

`client.supports(...)` / `providers_supporting(...)` and challenge-kind
tags. v1: probe by calling, catch exceptions.

## Client usage statistics

Status: new
Priority: -1

Cumulative solved/failed counters, Decimal cost totals, per-provider
breakdown; prefer an `on_event`-fed collector over client state.

## Deferred kinds: KeyCaptcha, Capy Puzzle, TikTok

Status: new
Priority: -1

Named candidates excluded from v1 (ADR-0070): single-provider, low
demand, or cookies-typed solutions. Third-party adapters may cover them
via the SDK.

## Deferred providers: DBC, azcaptcha, cap.guru, cptch.net, sctg.xyz, multibot

Status: new
Priority: -1

Named candidates excluded from v1 (ADR-0071): other protocol families or
unverified JSON-API mirrors. RuCaptcha is not here — verified working via
`base_url`.

## Image classification tasks

Status: new
Priority: -1

CapMonster `ComplexImageTask`, Capsolver `*Classification`, NopeCHA
recognition API. Distinct from token-solving kinds; third-party adapters
may cover via the SDK.

## Template automation tasks

Status: new
Priority: -1

Anti-Captcha AntiGate and CapMonster CustomTasks (DataDome, Imperva,
TenDI, ...). Needs a new task model, not a kind.

## Statistics endpoints

Status: new
Priority: -1

`getQueueStats` / `getAppStats` / `getSpendingStats` on the Anti-Captcha
surface; aux ops deliberately stop at balance + good/bad reports.

## CI coverage presentation/gating

Status: new
Priority: -1

pytest-cov stays informational only (ADR-0047); whether CI passes
`--cov`, what reports are shown/uploaded, and if a coverage threshold
becomes a gate — all undecided.

## Provider-fidelity verification method

Status: new
Priority: -1

A repeatable algorithm to verify adapter integrity against official API
docs and SDK clones (`var/vendor/repo/`): task-type strings, field wire names,
kind coverage, error-code tables. Golden-payload fixtures should be
derived from vendor sources, not hand-written twice.

## Observations backlog review

Status: new
Priority: -1

Review all accumulated observations — the `[open]`/`[needs-decision]`
markers across `spec/report/` (canonical list via
`grep -rn "\[open\]|\[needs-decision\]" spec/report/`) plus the
recurring refactor/tooling themes (shared JSON-family adapter base,
conftest `_fast_time`/`_fast_retry` consolidation,
`_fake`/`ScriptedAdapter` → `_myservice`, shared `ErrorKind` table,
`_internal/log.py`, markdown link checker in CI, README snippet
verification, facade-generation approach, provider-fidelity method) —
and turn each into a real `plan.md` task or remove it.