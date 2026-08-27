# Plan

Open tasks. A task is a record with a `##` header (task number + name), a
`Status:` line, the task body, and an optional `References:` line.

Statuses:

- `new` — not started; ready to pick up.
- `failed` — could not be completed as described; a `Reason:` line records
  why. Re-open by flipping back to `new` and clearing the reason.

A `done` task does not live here: when a task is finished, its record is
removed and archived into the report of the session that worked on it
(`spec/report/`).

Ordering: failed tasks first, then new; within a status, by task number.

## Task 17: Adapter golden-payload tests

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

## Task 18: README + CHANGELOG

Status: new

- README: finalized usage per the implemented API (universal + facade
  clients, kind list, two-phase batch, custom providers / adapter SDK,
  referral note, base-URL mirrors such as RuCaptcha).
- CHANGELOG: Keep-a-Changelog with an "Unreleased" section summarizing
  the v1 implementation; static version stays 0.1.0.
- Release-consistency CI guards: tag == pyproject version == matching
  CHANGELOG section.

References: ADR-0021, ADR-0022, ADR-0023, ADR-0072.