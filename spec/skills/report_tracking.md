# Report Tracking

Based on result of working session, compile a list of suggestions about how to change project environment, spec, tools, etc to help you build
things more effectively. Save this suggestions into new file in `spec/report/<year>/<month>/<day>/` directory.

Filename: `report-<epoch>-task-<N>.md` for an indexed implementation task,
`report-<epoch>-<slug>.md` for ad-hoc work requested directly by the user.

First line of report must be `## Report on task <task number>: <task title>`.
For ad-hoc work (not an indexed task), use
`## Report on task: <descriptive title>` instead.

Structure the suggestions under these categories, each item prefixed with
a status marker:

- `### Spec/ADR amendments` — spec/doc/ADR changes suggested.
- `### Future-task notes` — reminders for work that later tasks must do.
- `### Tooling/process` — environment, toolchain, or workflow learnings.

Item markers: `[open]` not yet addressed, `[acted]` already handled
(append a one-line note), `[needs-decision]` requires an owner decision.

When an `[open]` item is addressed or a `[needs-decision]` item is
decided, update the source report's marker (append a one-line note) *and*
refresh `spec/report/open.md` — the roll-up is never the only place a
status lives.

After writing the report, refresh `spec/report/open.md`: the roll-up of
every still-`[open]` / `[needs-decision]` item across all reports (one
line per item: category, task ref, one-liner, link to the source report).
