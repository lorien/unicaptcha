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