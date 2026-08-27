# Plan

Open tasks. A task is a record with a `##` header (task name), a `Status:`
line, the task body, and an optional `References:` line.

Statuses:

- `new` — not started; ready to pick up.

A `done` task does not live here: when a task is finished, its record is
removed and archived into the report of the session that worked on it
(`spec/report/`). A task leaves plan.md only when its work is complete and
committed.

Order in the file expresses priority: the topmost `new` task is picked
first. The owner reorders records to reprioritize.

Ad-hoc tasks requested directly by the user are not tracked here; their
reports live in `spec/report/`.

## README + CHANGELOG

Status: new

- README: finalized usage per the implemented API (universal + facade
  clients, kind list, two-phase batch, custom providers / adapter SDK,
  referral note, base-URL mirrors such as RuCaptcha).
- CHANGELOG: Keep-a-Changelog with an "Unreleased" section summarizing
  the v1 implementation; static version stays 0.1.0.
- Release-consistency CI guards: tag == pyproject version == matching
  CHANGELOG section.

References: ADR-0021, ADR-0022, ADR-0023, ADR-0072.