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
| [0001](ADR/0001-supported-providers.md) | Supported providers | 2Captcha, Anti-Captcha, CapMonster Cloud |
| [0002](ADR/0002-captcha-types-scope.md) | CAPTCHA types scope | image, text, reCAPTCHA v2/v3, hCaptcha |
| [0003](ADR/0003-sync-async-architecture.md) | Blocking sync + async-native architecture | no wrapper magic |
| [0004](ADR/0004-python-version-and-typing-policy.md) | Python 3.11+ and strict typing | mypy + pyright strict, py.typed |
| [0005](ADR/0005-universal-multi-provider-client.md) | Universal multi-provider client | registry, dispatch by challenge class; amended: 0052 |
| [0006](ADR/0006-provider-specific-challenge-classes.md) | Provider-specific challenge classes | frozen dataclasses |
| [0007](ADR/0007-provider-facades-via-composition.md) | Provider facades | amended: peers over SolveEngine |
| [0008](ADR/0008-rich-generic-result-objects.md) | Rich generic result objects | Result[T], Decimal cost |
| [0009](ADR/0009-unified-error-hierarchy.md) | Unified error hierarchy | amended: no SolveCancelledError, no UnknownTaskError |
| [0010](ADR/0010-timeouts-and-defaults.md) | Timeouts | amended: total_timeout semantics |
| [0011](ADR/0011-retry-and-polling-policy.md) | Retry and polling policy | amended: refined retry scope, full jitter |
| [0012](ADR/0012-proxy-handling.md) | Proxy handling | optional challenge field + client default |
| [0013](ADR/0013-auxiliary-operations.md) | Auxiliary operations | amended: TaskRef routing, four-state status |
| [0014](ADR/0014-api-key-hygiene.md) | API key hygiene | own SecretStr, no env helpers |
| [0015](ADR/0015-poll-only-no-webhooks.md) | Poll-only, no webhooks | |
| [0016](ADR/0016-cancellation-semantics.md) | Cancellation semantics | amended: pure propagation |
| [0017](ADR/0017-no-client-rate-limiting.md) | No client-side rate limiting | |
| [0018](ADR/0018-logging-and-events.md) | Logging and events | amended: flat logger, failed phase |
| [0019](ADR/0019-toolchain.md) | Toolchain | uv, ruff, pytest, respx, slotscheck |
| [0020](ADR/0020-mit-license.md) | MIT license | |
| [0021](ADR/0021-static-semver-versioning.md) | Static SemVer versioning | 0.1.0 start |
| [0022](ADR/0022-manual-changelog-with-ci-guards.md) | Manual changelog with CI guards | |
| [0023](ADR/0023-readme-only-docs.md) | README-only docs for v1 | |
| [0024](ADR/0024-network-knobs.md) | Network knobs | amended: mutual exclusion, per-request UA |
| [0025](ADR/0025-image-input-bytes-only.md) | Image input as bytes only | |
| [0026](ADR/0026-user-agent-and-repo-url.md) | User-Agent and repo URL | |
| [0027](ADR/0027-concurrency-guarantees.md) | Concurrency guarantees | |
| [0028](ADR/0028-no-proxy-validation.md) | No proxy validation | |
| [0029](ADR/0029-unsolvable-captcha-error.md) | UnsolvableCaptchaError | dedicated exception, no auto-resubmit |
| [0030](ADR/0030-numeric-defaults.md) | Numeric defaults table | |
| [0031](ADR/0031-field-surface-level.md) | Field surface specification level | |
| [0032](ADR/0032-taskstatus-split.md) | TaskStatus split from Result | amended: 0050, 0056 |
| [0033](ADR/0033-client-lifecycle.md) | Client lifecycle | amended: shutdown event, surviving registry |
| [0034](ADR/0034-result-surface-and-metadata.md) | Result surface and metadata | raw bytes, provider/created_at/elapsed |
| [0035](ADR/0035-solution-bases-non-instantiable.md) | Solution bases non-instantiable | amended: 0056 |
| [0036](ADR/0036-package-layout-and-naming.md) | Package layout and naming | *Client suffix everywhere; amended: 0052, 0054 |
| [0037](ADR/0037-duplicate-provider-kinds.md) | Duplicate provider kinds forbidden | amended: 0055 |
| [0038](ADR/0038-abandoned-task-registry.md) | Abandoned-task registry | bounded, surviving close |
| [0039](ADR/0039-logging-taxonomy.md) | Logging taxonomy | |
| [0040](ADR/0040-lenient-parsing-and-usd.md) | Lenient parsing and USD balance | |
| [0041](ADR/0041-public-internal-boundary-and-adapter-sdk.md) | Public/internal boundary + adapter SDK | amended: 0052, 0053 |
| [0042](ADR/0042-config-validation.md) | Config validation | InvalidConfigError; amended: 0052, 0053 |
| [0043](ADR/0043-config-shape-and-merge.md) | Config shape and merge semantics | None-able fields, field-wise merge |
| [0044](ADR/0044-event-attachment-and-parity.md) | Event handler attachment | constructor + per-call |
| [0045](ADR/0045-taskref-and-provider-validation.md) | TaskRef and provider validation | |
| [0046](ADR/0046-version-single-source-and-reference-adapter.md) | Version single source + reference adapter | |
| [0047](ADR/0047-ci-matrix-and-free-threaded.md) | CI matrix and free-threaded Python | |
| [0048](ADR/0048-challenge-kind-bases.md) | Challenge kind bases | symmetric with solutions |
| [0049](ADR/0049-http-config-mutual-exclusion.md) | HTTP config mutual exclusion | |
| [0050](ADR/0050-status-queries-answer.md) | Status queries answer, operations raise | |
| [0051](ADR/0051-facade-parameter-parity.md) | Facade parameter parity | |
| [0052](ADR/0052-adapter-naming.md) | Adapter naming | amends 0005/0036/0041/0042: `adapters=` kwarg, `<Provider>Adapter` |
| [0053](ADR/0053-adapter-contract-abc.md) | Adapter contract enforcement | `BaseAdapter` ABC; settles 0052 open question |
| [0054](ADR/0054-multiclient-naming.md) | MultiClient naming | amends 0036: `MultiClient`/`AsyncMultiClient` |
| [0055](ADR/0055-adapter-provider-attribute.md) | Adapter `provider` attribute | amends 0037/0041/0052/0053: `kind` renamed `provider` |
| [0056](ADR/0056-taskstatus-surface-and-basesolution.md) | TaskStatus surface + BaseSolution root | amends 0032/0035: no `Result` embedding, `TaskState` enum |

## Conventions

- Dates in ADRs reflect when the decision was settled (2026-08-22/23 design sessions).
- "Superseded by" links point forward; later ADRs link back to what they amend.
- The project is experimental: pre-1.0, no public API stability obligations. The
  public/internal boundary communicates intent, not commitment.
