# Task 2: Core models and public types

Status: new

Implement `unicaptcha/types.py` (re-exported from root):

- `TaskResult[T]`: `solution`, `task_id`, `cost` (`Decimal | None`,
  presence-check), `raw` (`bytes`), `provider`, `created_at`, `elapsed`,
  `task_ref` property.
- `TaskStatusResult`: `task_id`, `provider`, `status` (`TaskStatus`
  enum), `solution` (`BaseSolution | None`), `cost`, `raw`.
- `TaskRef`: public, constructible `(provider, task_id)`.
- `TaskTicket[T]`: `task_ref`, `submitted_at`, `instant_answer`; not
  user-constructible.
- `ParsedTask` and `SubmitAccepted` (adapter-SDK vocabulary).
- `Proxy` / `ProxyKind`: structured fields, fail-fast validation
  (`InvalidConfigError`).
- `SecretStr`: hand-rolled, full-mask repr/str, value equality,
  picklable; constructors wrap `SecretStr | str`.
- `NetworkConfig` / `TimeConfig` / `RetryConfig`: frozen, all-None-able,
  explicit bad values raise `InvalidConfigError` (ADR-0042); the
  field-wise None-merge resolution chain.
- repr policy: bytes stubs, `***abcd` token tail, fully masked keys.

References: ADR-0008, ADR-0032, ADR-0034, ADR-0043, ADR-0045, ADR-0050,
ADR-0056, ADR-0063, ADR-0067, ADR-0075, ADR-0014, ADR-0012.

## Done

- `unicaptcha/errors.py` (minimal root; task 3 extends): `ErrorKind` (13
  values per ADR-0009), `UnicaptchaError(kind, raw_response)`,
  `InvalidConfigError` — pulled forward because `Proxy`/config validation
  raise it.
- `unicaptcha/solution/base.py` (minimal root; task 6 extends): abstract
  `BaseSolution` (frozen dataclass; `__post_init__` raises `TypeError` when
  `type(self) is BaseSolution`, ADR-0035/0056) — pulled forward because
  `TaskStatusResult.solution` / `ParsedTask.solution` reference it.
- `unicaptcha/types.py`: `TaskStatus` enum (PENDING/READY/NO_SOLUTION/
  UNKNOWN), `TaskRef`, `TaskResult[T]` (T bound BaseSolution; `task_ref`
  property), `TaskStatusResult`, `TaskTicket[T]` (doc-only
  non-constructibility — deliberate ADR-0067 deviation, see report),
  `ParsedTask`/`SubmitAccepted` (adapter-SDK vocabulary, slots),
  `Proxy`/`ProxyKind` (host non-empty, port 1..65535 -> InvalidConfigError),
  `SecretStr` (full-mask repr/str, strict equality), `NetworkConfig`/
  `TimeConfig`/`RetryConfig` (all None-able; explicit bad values ->
  InvalidConfigError incl. `backoff_cap >= backoff_base`, `poll_delay >= 0`).
- `unicaptcha/_internal/repr.py`: `stub_bytes` / `truncate_token` helpers
  for the repr policy (ADR-0034); used by public reprs now, by solution
  kinds (task 6) later.
- `unicaptcha/_internal/config.py`: `merge_configs` — pure field-wise
  None-merge (ADR-0043); engine (task 9) will use it for the resolution
  chain.
- Root `__init__.py` re-exports the new vocabulary (types + errors +
  `BaseSolution`) per ADR-0036.
- Tests: 72 passing — types, proxy, config (validation + merge), SecretStr
  (masking, strict-equality semantics, hash, pickle), TaskRef, pickle
  round-trips for the frozen-data vocabulary, repr helpers, BaseSolution,
  errors, root exports.
- Full suite green (ruff, mypy strict, pyright strict, slotscheck, pytest).
  No hard-coded credentials.