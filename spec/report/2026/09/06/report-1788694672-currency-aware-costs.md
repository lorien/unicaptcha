## Report on task: Currency-aware costs

### Task (archived from plan.md)

Status: done

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

### Investigation

- The provider wire returns **bare numbers only** — 2Captcha's official
  `getBalance`/`getTaskResult` docs return `"balance": 0.93958` and
  `cost` as a bare string, no currency code. Currency therefore can
  never be parsed; it must be declared.
- The currency is per-service, not a per-account API-visible setting:
  canonical API hosts are `api.2captcha.com` (USD), `api.rucaptcha.com`
  (RUB mirror), `api.anti-captcha.com`, `api.capmonster.cloud`,
  `api.capsolver.com`. Owner decided: no normalization, no `api.`-prefix
  manipulation; RuCaptcha is referenced only as `api.rucaptcha.com` in
  all user-facing docs.

### Done

- New public `Money(amount: Decimal, currency: str)` in
  `unicaptcha/types.py` (frozen, plain value type — no arithmetic, so
  cross-currency mixing is impossible); exported from the root.
- `TaskResult.cost`, `TaskStatusResult.cost`, `ParsedTask.cost`:
  `Decimal | None` → `Money | None`.
- `BaseAdapter`: `default_currency: ClassVar[str] = "USD"`,
  `_host_currency: ClassVar[Mapping[str, str]] = {}`, `currency=`
  constructor kwarg; `self.currency` resolves kwarg → exact base_url-host
  match → class default. `_money()` helper wraps parsed costs.
  `TwoCaptchaAdapter._host_currency = {"api.rucaptcha.com": "RUB"}`.
- `TaskEvent.cost: Money | None`, set only on `RESULT_RECEIVED` (both
  engines: instant-answer and wait-loop sites pass `parsed.cost`).
- `get_balance()` → `Money` on `Solver`, `AsyncSolver`, and the 8
  facades; engines wrap the parsed `Decimal` with `adapter.currency`.
  The parse layer (`parse_balance`, `_decimal`) stays `Decimal` —
  third-party adapter contract unchanged.
- `unicaptcha/stats.py`: `ProviderUsage` gains `cost: Decimal | None` +
  `currency: str | None`; `UsageStats` gains `cost_totals:
  Mapping[str, Decimal]` (per-currency cumulative, `default_factory`).
  `StatsCollector` sums `event.cost.amount` per provider and per
  currency — never a blind cross-currency sum.
- Docs/README/CHANGELOG/ADR: RuCaptcha example fixed to
  `base_url="https://api.rucaptcha.com"` (README, docs/index); money
  typed in universal-client/facades/events guides + api/types; breaking
  CHANGELOG entry; ADR-0040 amended (verification note resolved,
  currency-aware contract).
- Tests: `tests/test_currency.py` (Money equality/repr/frozen, host
  derived USD/RUB, `currency=` override, other-provider USD, unknown
  mirror fallback, per-instance); `tests/test_stats.py` cost totals
  (per-provider + per-currency incl. mixed USD/RUB, failures add no
  cost, reset). Existing cost/balance assertions updated `Decimal` →
  `Money(…, "USD")` across the suite.

### Verification

`uv run ./scripts/check.sh` — ruff, mypy, pyright, slotscheck, pytest:
all pass (579 passed, 7 integration deselected). `uv run mkdocs build`
clean.

### Spec/ADR amendments

- ADR-0040: "Currency-aware costs amendment (2026-09-06)" — verification
  note resolved; `Money` contract; per-service host defaults; no
  conversion; parse layer stays `Decimal`.

### Future-task notes

- None — the "Currency-aware costs" record is fully resolved.