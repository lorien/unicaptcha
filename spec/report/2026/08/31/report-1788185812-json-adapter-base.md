## Report on task: Shared JSON-family adapter base

Closed the plan.md record of the same name. The four JSON adapters
(2Captcha, Anti-Captcha, CapMonster, Capsolver) duplicated near-identical
helpers (`_decode`, `_decimal`, `_proxy_fields`, `_cookies`, `_soft_id`,
`_single_token`, `_solution_dict`, `_task_id`, `_provider_code`,
`_provider_message`) and the whole response-parsing pipeline
(`parse_submit_response`, `parse_task_status`, `parse_balance`,
`map_provider_error`, `build_payload`).

### Done

- New public `JsonAdapterBase(BaseAdapter)` in `unicaptcha/adapter.py`
  (re-exported from the package root). Provides the shared pipeline and
  field helpers; subclasses declare `json_provider`, `error_kinds`,
  `unknown_task_codes` (and optionally `project_soft_id`) and supply the
  per-provider `_build_task` / `_solution_from`. Error-message strings
  preserved via `json_provider` labels.
- `error_from_kind` moved to public `unicaptcha/errors.py`;
  `_internal/errors.py` is now a re-export shim (engines + tests keep
  working). This closes the ADR-0041 gap where third-party adapters could
  not raise mapped provider errors without touching `_internal`.
- The four adapters subclass `JsonAdapterBase` and delete the duplicated
  helpers/pipeline (~389 net lines removed):
  - twocaptcha: overrides `_extra_envelope` (envelope `languagePool`).
  - anticaptcha: overrides `_proxy_fields` (IP-only rule; error message now
    uses the provider label instead of the challenge class name — nothing
    asserted the old wording).
  - capmonster: inherits everything (proxyless).
  - capsolver: overrides `_task_id` (UUID, `int | str`),
    `parse_task_status` (`status: "failed"` -> NO_SOLUTION), `_soft_id`
    (embeds nothing, ADR-0072 parity).
  - Side benefit: the shipped adapters no longer import `_internal` at all
    (previously `_internal.errors`).
- Tests: two guards in `test_package.py` — the four adapters subclass
  `JsonAdapterBase`; the base is abstract (cannot be instantiated).
- Docs: architecture.md §9 (layout tree, public-surface bullet, Adapter
  SDK snippet) and CHANGELOG Unreleased **Changed** entry.

### Verification

`uv run ruff check .` / `ruff format --check` / `mypy unicaptcha` /
`pyright` / `slotscheck unicaptcha` / `uv run pytest` — all pass
(489 passed, 7 integration deselected). The golden-payload and per-provider
behavior suites validate the wire contract is unchanged.

### Future-task notes

- The reference adapter `tests/_myservice.py` still subclasses
  `BaseAdapter` directly; it could now switch to `JsonAdapterBase` as the
  documented third-party pattern (out of scope here — behavior already
  covered).
- Related plan records "Shared ErrorKind mapping table" and "conftest
  fast-config consolidation" remain open; the ErrorKind table task could
  now build on `JsonAdapterBase.error_kinds`.