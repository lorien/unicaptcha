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

## `_internal/log.py`

Status: new
Priority: -1

A shared module for the flat `unicaptcha` logger if call sites
proliferate (ADR-0018/0039 keep it flat; extract only on need).

## Universal `solve()` kind overloads

Status: new
Priority: -1

Universal-tier `solve` returns `TaskResult[Any]` statically (runtime fully
typed). Add the nine-kind overload set if universal precision is wanted;
facades already type precisely.

## Register project soft_ids for Anti-Captcha and CapMonster Cloud

Status: new
Priority: -1

2Captcha/RuCaptcha soft_id 5859 is integrated (report-1788542943). Both
Anti-Captcha and CapMonster Cloud support a per-request `softId`
(referral embedding, ADR-0072), so their project ids can be registered
the same way:

- Anti-Captcha: `softId` field, 10% commission. Register at
  https://anti-captcha.com/clients/tools/devcenter (confirmed via the
  anticaptcha-python vendor examples).
- CapMonster Cloud: `softId` confirmed in the vendor SDK
  (var/vendor/repo/capmonster-python-captcha-solver/
  capmonstercloud_client/clientOptions.py — default_soft_id=55, sent in
  the createTask envelope); affiliate program up to 30% (register in
  their developer dashboard).
- Capsolver: no affiliate field.

When the ids are obtained: set `AntiCaptchaAdapter.project_soft_id` and
`CapMonsterAdapter.project_soft_id`; update the respective default
payload / golden tests (mirror the 5859 change: the compat base already
sends `softId` from the registered id); add a CHANGELOG [Unreleased]
entry. Both adapters inherit the `_soft_id`/`project_soft_id`
machinery — one-line code change each.

References: ADR-0072, report-1788542943 (soft_id 5859),
var/vendor/anticaptcha-python-analysis.md,
var/vendor/capmonster-python-captcha-solver-analysis.md.

## Currency-aware costs

Status: new
Priority: -1

ADR-0040 pins balance — and, by inheritance, `TaskResult.cost` — to USD
("no currency field, no conversion"), but its implementation-time
verification note was never acted on: provider cost/balance currencies
are unverified, and accounts can be currency-scoped by registration
(2Captcha/RuCaptcha report RUB for RUB-scoped accounts), so summing
costs across providers silently mixes currencies.

Resolve the contract (ADR-0040 candidate shapes: per-provider documented
currency, or `tuple[Decimal, str]`), then extend the client usage
statistics to count cost: add `cost` to `TaskEvent` (set only on
`RESULT_RECEIVED`; the engine already holds `parsed.cost` at the emit
site) and total costs per provider and cumulatively in `UsageStats`.

References: ADR-0040 (verification note), report-1788684317
(client usage statistics).