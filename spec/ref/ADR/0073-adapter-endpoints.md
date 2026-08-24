# ADR-0073: Adapter `Endpoints` declaration

**Status:** Accepted (amends ADR-0053)
**Date:** 2026-08-23

## Context

The adapter contract covers the JSON body (`build_payload`) and the
base URL (`base_url`), but nothing in the design said who owns the
request **paths** (`/createTask`, `/getTaskResult`, ...). All four
shipped providers share the JSON-family convention, so the gap was
invisible — but a third-party adapter for a provider with divergent
paths could not express them through the SDK. (Competitor libraries
build URLs inside per-request classes: `BASE_URL + "/createTask"`
scattered across the codebase.)

## Decision

- **`Endpoints`** — frozen dataclass, all fields required (no field
  defaults), keyed by our operation names so every key answers
  "where does this operation go?":

```python
@dataclass(frozen=True)
class Endpoints:
    submit: str                # solve() / submit() post here
    get_task_result: str       # wait() / wait_ref() / get_task_result() poll here
    get_balance: str           # get_balance() asks here
    report_good_result: str    # report_good_result() sends praise here
    report_bad_result: str     # report_bad_result() complains here
```

- `BaseAdapter.endpoints: ClassVar[Endpoints]` carries the
  **JSON-family default** (`/createTask`, `/getTaskResult`,
  `/getBalance`, `/reportCorrect`, `/reportIncorrect`) — fits all
  four shipped providers, who declare nothing.
- **All-or-nothing override** (owner decision): an adapter either
  inherits the default entirely or declares a complete `Endpoints(...)`
  with all five paths. No per-field merging — a custom set is a
  deliberate statement about a divergent provider; partial overrides
  would mix provenance (half ours, half theirs), harder to audit.
  Enforced by the dataclass having no field defaults.
- **The engine owns the join**: `adapter.base_url +
  adapter.endpoints.<field>`. `base_url` stays orthogonal — the
  RuCaptcha mirror override is unaffected.
- Providers lacking an operation (e.g. no report endpoint) still fill
  the field — harmless, because `report_*_supported()` gates usage;
  a placeholder value is acceptable and documented.
- **Static strings only**: path-parameterized URLs (DBC-style
  `/captcha/{id}/report`) are not expressible; URL-builder methods
  are the recorded evolution path if such a provider ever enters
  scope.

## Rationale

- Closes the ownership gap with pure data: a path string is data, the
  adapter stays a pure translator (ADR-0041), and the default makes
  the common case declare nothing.
- Operation-keyed names (Scheme A) over provider-jargon names
  (Scheme B: `create_task`, `report_correct`, ...): the adapter
  author writing a custom set thinks in our operations; two of five
  keys already matched.

## Alternatives considered

- **Hardcoded paths in the engine**: rejected; third-party adapters
  for divergent providers become inexpressible.
- **URL-builder methods** (`build_task_result_url(task_id)`, ...):
  rejected for v1; five more contract methods serving zero shipped
  users. Their one genuine power — argumentized paths — is recorded
  as the evolution path instead.
- **`Endpoints` with per-field defaults** (partial override):
  rejected by owner; mixed provenance is harder to audit than a
  complete deliberate set.
- **Provider-protocol key names** (Scheme B): rejected; adapter
  authors think in our operations, not provider jargon.
