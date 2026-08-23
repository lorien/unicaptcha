# Deferred decisions

Canonical list of explicitly deferred items. Deferred means: not part of v1,
revisit deliberately later. Anything not listed here and not in an ADR was
never discussed.

| # | Item | Notes |
|---|---|---|
| 1 | PyPI publishing / release automation flow | Whether a `v*` tag triggers automated publish, TestPyPI dry-run, trusted publishing vs token. Deliberately postponed ("other day"). |
| 2 | Exact per-provider challenge field lists | Which fields each provider's challenge classes carry beyond the universal kind-base fields (2Captcha's `lang`, `hint`, `phrase`, `numeric`, `math`, `min_len`, `max_len`, `case_sensitive`; CapMonster capability flags; etc.). Worked out during implementation against each provider's API reference. Includes the worker-context surface (`user_agent`/`cookies` per provider, ADR-0069). |
| 3 | `examples/` directory | Use-case examples; nature undecided (runnable scripts vs illustrative snippets). Directory name must be `examples/`. |
| 4 | Automatic provider selection / failover routing | Kind-level random selection now exists (ADR-0064: `provider=None` picks uniformly among supporting adapters). Still deferred: *policy* routing — cheapest-first, failover, load balancing, stickiness/weighting. A strategy wrapper could be added as a purely additive layer. |
| 5 | Client-side rate limiting / concurrency caps | v1: no `max_parallel_solves`, no request spacing. Callers manage concurrency; `RateLimitError` retry with backoff exists as a safety net. Documented guidance only. |
| 6 | API-key rotation | One key per provider instance in v1. Rotation can be added later as a provider-level wrapper. |
| 7 | Webhook/pingback solve mode | v1 is strictly poll-based. The submit/await separation now also has a public face (ADR-0067), keeping a webhook mode additive if ever added. |
| 8 | Hierarchical logger names | v1 uses one flat `unicaptcha` logger. Component-hierarchy names (`unicaptcha.http`, `unicaptcha.providers.twocaptcha`, ...) rejected for now to avoid scope creep; revisit if per-component filtering is requested. |
| 9 | `unicaptcha.testing` module | Fake clients / canned results / failure injection for downstream test suites. Defer until core API survives real usage. |
| 10 | ~~Granular `submit_timeout` / `solve_timeout` split~~ | **Closed by ADR-0067**: the two-phase `submit()`/`wait()` API realizes the split as two calls with separate budgets; no config knobs needed. |
| 11 | Capability introspection API | `client.supports(...)` / `providers_supporting(...)` and challenge-kind tags. v1: probe by calling, catch exceptions. |
| 12 | Client usage statistics | Cumulative solved/failed counters, Decimal cost totals, per-provider breakdown. v1: events + logging are the observability story. If added, prefer an `on_event`-fed collector over client state. |
| 13 | Deferred CAPTCHA kinds: KeyCaptcha, Capy Puzzle, TikTok | Named candidates excluded from v1 (ADR-0070): KeyCaptcha/Capy are single-provider, low demand; TikTok has a cookies-typed solution (no payload field, secrets-adjacent repr questions). Third-party adapters may cover them via the SDK meanwhile. |
