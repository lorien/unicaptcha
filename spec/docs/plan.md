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

## Release-consistency CI guards

Status: new

Add a `release-check` job to `.github/workflows/ci.yml` running on `v*`
tag pushes: tag == `unicaptcha/_version.py` version == matching
`## [{version}]` CHANGELOG section.

References: ADR-0021, ADR-0022.