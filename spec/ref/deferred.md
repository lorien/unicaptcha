# Deferred decisions

Canonical list of explicitly deferred items. Deferred means: not part of v1,
revisit deliberately later. Anything not listed here and not in an ADR was
never discussed.

| # | Item | Notes |
|---|---|---|
| 1 | PyPI publishing / release automation flow | Whether a `v*` tag triggers automated publish, TestPyPI dry-run, trusted publishing vs token. Deliberately postponed ("other day"). |
| 2 | Exact per-provider challenge field lists | Which fields each provider's challenge classes carry beyond the universal kind-base fields (2Captcha's `lang`, `hint`, `phrase`, `numeric`, `math`, `min_len`, `max_len`, `case_sensitive`; CapMonster capability flags; etc.). Worked out during implementation against each provider's API reference. |
| 3 | `examples/` directory | Use-case examples; nature undecided (runnable scripts vs illustrative snippets). Directory name must be `examples/`. |
| 4 | Automatic provider selection / failover routing | Callers route explicitly by constructing provider-specific challenges in v1. A strategy wrapper (cheapest-first, failover, load balancing) could be added as a purely additive layer. |
| 5 | Client-side rate limiting / concurrency caps | v1: no `max_parallel_solves`, no request spacing. Callers manage concurrency; `RateLimitError` retry with backoff exists as a safety net. Documented guidance only. |
| 6 | API-key rotation | One key per provider instance in v1. Rotation can be added later as a provider-level wrapper. |
| 7 | Webhook/pingback solve mode | v1 is strictly poll-based. If added later, the submit/await separation in the engine keeps it additive. |
| 8 | Hierarchical logger names | v1 uses one flat `unicaptcha` logger. Component-hierarchy names (`unicaptcha.http`, `unicaptcha.providers.twocaptcha`, ...) rejected for now to avoid scope creep; revisit if per-component filtering is requested. |
| 9 | `unicaptcha.testing` module | Fake clients / canned results / failure injection for downstream test suites. Defer until core API survives real usage. |
| 10 | Granular `submit_timeout` / `solve_timeout` split | v1 has a single `total_timeout` covering submit + polling. Field-wise-merge config design leaves room for the split without breaking changes. |
| 11 | Capability introspection API | `client.supports(...)` / `providers_supporting(...)` and challenge-kind tags. v1: probe by calling, catch exceptions. |
| 12 | Client usage statistics | Cumulative solved/failed counters, Decimal cost totals, per-provider breakdown. v1: events + logging are the observability story. If added, prefer an `on_event`-fed collector over client state. |
