# Task 17: Adapter golden-payload tests

Status: new

respx transport-level tests for all five adapters (four providers +
reference "myservice"):

- Exact outgoing URL + JSON payload assertions per kind × provider
  against the ADR-0076 field tables (universal→wire mapping, provider
  extras, proxy/worker-context serialization, referral embedding).
- Response parsing: `SubmitAccepted` (incl. `instant_answer`),
  `ParsedTask` state machine (pending/ready/unsolvable/unknown), balance,
  report bad/good; malformed/wrong-shape bodies → `ProviderError` with
  `raw_response` and chained cause.
- Error mapping per provider (rate-limit, busy, auth, balance) and the
  support matrix (report `*_supported`, unsupported kinds raise
  `UnsupportedChallengeError`).

References: ADR-0019, ADR-0040, ADR-0058, ADR-0068, ADR-0072, ADR-0075,
ADR-0076.