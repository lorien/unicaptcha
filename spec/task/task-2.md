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