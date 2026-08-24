# unicaptcha knowledge base

This directory is the design knowledge base for the unicaptcha project. It records
what the project is, how it is designed, and why each decision was made.

## Documents

| Document | Purpose |
|---|---|
| [goals.md](goals.md) | Motivation, goals, non-goals, target users, v1 scope |
| [architecture.md](architecture.md) | Complete technical design: components, models, flows, defaults, toolchain |
| [deferred.md](deferred.md) | Canonical list of explicitly deferred decisions |
| [ADR/](ADR/) | Architecture Decision Records, one per settled decision |

## ADR directory

Each ADR follows the template: Status / Context / Decision / Rationale /
Alternatives considered. Amendments explicitly mark which earlier decision they
supersede.

| ADR | Topic | Notes |
|---|---|---|
| [0001](ADR/0001-supported-providers.md) | Supported providers | 2Captcha, Anti-Captcha, CapMonster, Capsolver; amended: 0071 |
| [0002](ADR/0002-captcha-types-scope.md) | CAPTCHA types scope | 9 kinds, enterprise flags; amended: 0070, 0074 |
| [0003](ADR/0003-sync-async-architecture.md) | Blocking sync + async-native architecture | no wrapper magic |
| [0004](ADR/0004-python-version-and-typing-policy.md) | Python 3.11+ and strict typing | mypy + pyright strict, py.typed |
| [0005](ADR/0005-universal-multi-provider-client.md) | Universal multi-provider client | registry, dispatch by challenge class; amended: 0052, 0064 |
| [0006](ADR/0006-provider-specific-challenge-classes.md) | Provider-specific challenge classes | frozen dataclasses; amended: 0048, 0066 |
| [0007](ADR/0007-provider-facades-via-composition.md) | Provider facades | amended: peers over SolveEngine |
| [0008](ADR/0008-rich-generic-result-objects.md) | Rich generic result objects | Result[T], Decimal cost |
| [0009](ADR/0009-unified-error-hierarchy.md) | Unified error hierarchy | amended: no SolveCancelledError, no UnknownTaskError; 0057; ServiceBusyError per 0059; EmptySolutionError per 0040 |
| [0010](ADR/0010-timeouts-and-defaults.md) | Timeouts | amended: total_timeout semantics; scoped to solve() by 0067 |
| [0011](ADR/0011-retry-and-polling-policy.md) | Retry and polling policy | amended: refined retry scope, full jitter; 0059 |
| [0012](ADR/0012-proxy-handling.md) | Proxy handling | optional challenge field + client default; amended: 0069 |
| [0013](ADR/0013-auxiliary-operations.md) | Auxiliary operations | amended: TaskRef routing, four-state status; 0057, 0068 |
| [0014](ADR/0014-api-key-hygiene.md) | API key hygiene | own SecretStr, no env helpers; amended: 0063 |
| [0015](ADR/0015-poll-only-no-webhooks.md) | Poll-only, no webhooks | |
| [0016](ADR/0016-cancellation-semantics.md) | Cancellation semantics | amended: pure propagation |
| [0017](ADR/0017-no-client-rate-limiting.md) | No client-side rate limiting | |
| [0018](ADR/0018-logging-and-events.md) | Logging and events | amended: flat logger, failed phase; 0067 |
| [0019](ADR/0019-toolchain.md) | Toolchain | uv, ruff, pytest, respx, slotscheck; amended: test-style commitments |
| [0020](ADR/0020-mit-license.md) | MIT license | |
| [0021](ADR/0021-static-semver-versioning.md) | Static SemVer versioning | 0.1.0 start |
| [0022](ADR/0022-manual-changelog-with-ci-guards.md) | Manual changelog with CI guards | |
| [0023](ADR/0023-readme-only-docs.md) | README-only docs for v1 | |
| [0024](ADR/0024-network-knobs.md) | Network knobs | amended: mutual exclusion, per-request UA, per-stage timeout semantics |
| [0025](ADR/0025-image-input-bytes-only.md) | Image input as bytes only | amended: 0065 |
| [0026](ADR/0026-user-agent-and-repo-url.md) | User-Agent and repo URL | |
| [0027](ADR/0027-concurrency-guarantees.md) | Concurrency guarantees | |
| [0028](ADR/0028-no-proxy-validation.md) | No proxy validation | |
| [0029](ADR/0029-unsolvable-captcha-error.md) | UnsolvableCaptchaError | dedicated exception, no auto-resubmit |
| [0030](ADR/0030-numeric-defaults.md) | Numeric defaults table | amended: 0070 adds FunCaptcha/GeeTest rows; poll_delay column; draft token-kind rows (2026-08-24) pending review — deferred item 15 |
| [0031](ADR/0031-field-surface-level.md) | Field surface specification level | |
| [0032](ADR/0032-taskstatus-split.md) | TaskStatus split from Result | amended: 0050, 0056 |
| [0033](ADR/0033-client-lifecycle.md) | Client lifecycle | amended: shutdown event, surviving registry |
| [0034](ADR/0034-result-surface-and-metadata.md) | Result surface and metadata | raw bytes, provider/created_at/elapsed; amended: cost presence-check |
| [0035](ADR/0035-solution-bases-non-instantiable.md) | Solution bases non-instantiable | amended: 0056 |
| [0036](ADR/0036-package-layout-and-naming.md) | Package layout and naming | *Client suffix everywhere; amended: 0052, 0054 |
| [0037](ADR/0037-duplicate-provider-kinds.md) | Duplicate provider kinds forbidden | amended: 0055 |
| [0038](ADR/0038-abandoned-task-registry.md) | Abandoned-task registry | bounded, surviving close; deferral ≠ abandonment per 0067 |
| [0039](ADR/0039-logging-taxonomy.md) | Logging taxonomy | |
| [0040](ADR/0040-lenient-parsing-and-usd.md) | Lenient parsing and USD balance | amended: currency note; EmptySolutionError; required fields |
| [0041](ADR/0041-public-internal-boundary-and-adapter-sdk.md) | Public/internal boundary + adapter SDK | amended: 0052, 0053 |
| [0042](ADR/0042-config-validation.md) | Config validation | InvalidConfigError; amended: 0052, 0053 |
| [0043](ADR/0043-config-shape-and-merge.md) | Config shape and merge semantics | None-able fields, field-wise merge; amended: poll_delay |
| [0044](ADR/0044-event-attachment-and-parity.md) | Event handler attachment | constructor + per-call |
| [0045](ADR/0045-taskref-and-provider-validation.md) | TaskRef and provider validation | amended: 0064; TaskTicket per 0067 |
| [0046](ADR/0046-version-single-source-and-reference-adapter.md) | Version single source + reference adapter | |
| [0047](ADR/0047-ci-matrix-and-free-threaded.md) | CI matrix and free-threaded Python | |
| [0048](ADR/0048-challenge-kind-bases.md) | Challenge kind bases | symmetric with solutions; amended: 0064 |
| [0049](ADR/0049-http-config-mutual-exclusion.md) | HTTP config mutual exclusion | |
| [0050](ADR/0050-status-queries-answer.md) | Status queries answer, operations raise | |
| [0051](ADR/0051-facade-parameter-parity.md) | Facade parameter parity | extended to submit/wait/wait_ref by 0067 |
| [0052](ADR/0052-adapter-naming.md) | Adapter naming | amends 0005/0036/0041/0042: `adapters=` kwarg, `<Provider>Adapter` |
| [0053](ADR/0053-adapter-contract-abc.md) | Adapter contract enforcement | `BaseAdapter` ABC; settles 0052 open question; amended: 0063, 0068, 0072, 0073, 0075 |
| [0054](ADR/0054-multiclient-naming.md) | MultiClient naming | superseded by 0062 |
| [0055](ADR/0055-adapter-provider-attribute.md) | Adapter `provider` attribute | amends 0037/0041/0052/0053: `kind` renamed `provider` |
| [0056](ADR/0056-taskstatus-surface-and-basesolution.md) | TaskStatus surface + BaseSolution root | amends 0032/0035: no `Result` embedding, `TaskState` enum |
| [0057](ADR/0057-unsupported-captcha-error-scope.md) | UnsupportedCaptchaError scope | amends 0009/0013/0053: client-side gaps included |
| [0058](ADR/0058-unknown-state-and-solve-poll.md) | UNKNOWN state in adapter contract | 4-state parse_task_result; solve-poll fail-fast; ParsedTask typed per 0075 |
| [0059](ADR/0059-rate-limit-retry.md) | Rate-limit retry | amends 0011: 429 + provider payloads retryable; ServiceBusyError amendment |
| [0060](ADR/0060-registry-advisory-and-recovery.md) | Registry advisory + recovery | amends 0033/0038: per-client semantics, workflow |
| [0061](ADR/0061-facade-constructor-parity.md) | Facade constructor parity | amends 0051: api_key/base_url + all client kwargs; amended: 0063, 0072 |
| [0062](ADR/0062-captchasolver-naming.md) | CaptchaSolver naming | supersedes 0054 class names; amends 0036 |
| [0063](ADR/0063-str-api-key.md) | Plain str api_key | amends 0014/0053/0061: union, boundary wrapping |
| [0064](ADR/0064-kind-solve-and-provider-selection.md) | Kind-level solve + provider selection | amends 0005/0045/0048; random among supporting adapters |
| [0065](ADR/0065-path-body.md) | Path accepted for image bodies | amends 0025: `bytes \| Path`, normalized to bytes |
| [0066](ADR/0066-challenge-call-style.md) | Challenge call-style | amends 0006: keyword-only fields, positional payload |
| [0067](ADR/0067-two-phase-submit-wait.md) | Two-phase submit/wait | TaskTicket; amends 0010/0018/0038/0045/0051; closes deferred 10; poll-delay skip; amended: 0075 |
| [0068](ADR/0068-report-good-result.md) | report_good_result | amends 0013/0053: bool return, adapter report pairs |
| [0069](ADR/0069-worker-context.md) | Worker context parameters | amends 0012: `user_agent`/`cookies` challenge fields |
| [0070](ADR/0070-kind-taxonomy-expansion.md) | Kind taxonomy expansion | amends 0002/0030: FunCaptcha, GeeTest v3/v4, enterprise flags; amended: 0074 |
| [0071](ADR/0071-capsolver-provider.md) | Capsolver provider | amends 0001: 4th provider; RuCaptcha v2 verified |
| [0072](ADR/0072-referral-embedding.md) | Referral embedding | amends 0053/0061: trinary `referral` kwarg, on by default |
| [0073](ADR/0073-adapter-endpoints.md) | Adapter Endpoints | amends 0053: operation-keyed paths, all-or-nothing override |
| [0074](ADR/0074-turnstile-kind.md) | Cloudflare Turnstile kind | amends 0002/0070: ninth v1 kind; resolves dangling deferred claim |
| [0075](ADR/0075-submit-ready-fast-path.md) | Submit-ready fast path | amends 0053/0067, formalizes ParsedTask (0058): SubmitAccepted, ticket-carried `ready` |

## Conventions

- Dates in ADRs reflect when the decision was settled (2026-08-22/23 design sessions).
- "Superseded by" links point forward; later ADRs link back to what they amend.
- The project is experimental: pre-1.0, no public API stability obligations. The
  public/internal boundary communicates intent, not commitment.
