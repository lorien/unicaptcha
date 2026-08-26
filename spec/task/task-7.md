# Task 7: Adapter SDK contract

Status: new

Implement the public `BaseAdapter` ABC:

- Class attrs: `provider`, `challenges`, `default_task_config`,
  `endpoints` (operation-keyed, all-or-nothing override).
- Constructor: `api_key: SecretStr | str` (wrapped at boundary),
  `base_url` override, trinary `referral` (on by default); key-masking
  `repr`.
- Translation methods: `build_payload`, `parse_submit_response` →
  `SubmitAccepted` (incl. `instant_answer`), `parse_task_status` →
  `ParsedTask`, `parse_balance`, `map_provider_error`, report bad/good
  pairs with `*_supported` matrix (default-unsupported concrete).
- Registration contract: `Solver(adapters=[...])`; non-adapters raise
  `TypeError`.
- Runtime dependency check: no `_internal` imports by the SDK surface.

References: ADR-0041, ADR-0053, ADR-0055, ADR-0063, ADR-0068, ADR-0072,
ADR-0073, ADR-0075, ADR-0058.

## Done

- `unicaptcha/adapter.py` (singular; one-concern file — owner decision over
  the root-plural naming rule): the public adapter SDK surface.
- `Endpoints`: frozen dataclass, five required operation-keyed paths, no
  field defaults (ADR-0073 all-or-nothing); JSON-family default declared
  on `BaseAdapter.endpoints`.
- `BaseAdapter(ABC)` (ADR-0053):
  - Required ClassVars (`provider`, `challenges`, `default_base_url`)
    enforced via `__init_subclass__` -> `TypeError` at class creation.
  - Concrete `__init__(api_key, base_url=None, *, referral=True)`: plain
    `str` wrapped into `SecretStr` (ADR-0063), `base_url` defaulted to
    `default_base_url`, trinary `referral` stored (keyword-only — owner
    decision, consistent with ADR-0066/0043; one-line ADR-0053 signature
    tweak suggested). `__slots__` on the three stored attrs.
  - Concrete `__repr__`/`__str__` with fully masked key (ADR-0014).
  - Five abstract translation methods; `map_provider_error` returns
    `tuple[ErrorKind, str]` (kind + message).
  - Six concrete default-unsupported report methods (bad/good pairs,
    ADR-0068): `*_supported` -> False; build/parse raise
    `UnsupportedChallengeError`.
- Root re-exports `BaseAdapter`, `Endpoints`.
- No `_internal` imports in `adapter.py`; AST test pins it.
- Registration `TypeError` check for non-adapters deferred to the
  universal clients (tasks 9/10).
- Tests (144 total passing): Endpoints required-fields/frozen/default,
  ABC non-instantiable, missing-abstract-method fails, `__init_subclass__`
  enforcement per required ClassVar, constructor (wrap/passthrough/base_url
  default+override/referral kw-only), masked repr, report-pair defaults,
  SDK-module isolation, root exports.
- Full suite green (ruff, mypy strict, pyright strict, slotscheck, pytest).
  No hard-coded credentials.