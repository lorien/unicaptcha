# Report Tracking

Based on result of a working session, compile a list of suggestions about
how to change project environment, spec, tools, etc to help you build
things more effectively. Save this suggestions into new file in
`spec/report/<year>/<month>/<day>/` directory.

A report is written only when a task's work is complete and committed. It
is also the archive of the task it worked on: when a task from
`spec/docs/plan.md` is done, its record is removed from the plan and
stored here. Ad-hoc work (not in the plan) has no record to archive; its
report documents the work and suggestions directly. Blocked or unfinished
work does not produce a report.

Filename: `report-<epoch>-<slug>.md`, where `<slug>` is a short
hyphenated identifier of the task (plan task or ad-hoc work).

First line of report must be `## Report on task: <title>`.

## Structure

For a task from plan.md, the report opens with the archived task record,
then what was done, then the suggestions:

- `### Task (archived from plan.md)` — the original task header and body
  with `Status: done`, moved here verbatim when the task finished.
- `### Done` — a brief list of things done during the work on the task.
- `### Spec/ADR amendments` — spec/doc/ADR changes suggested.
- `### Future-task notes` — reminders for work that later tasks must do.
- `### Tooling/process` — environment, toolchain, or workflow learnings.

For ad-hoc work, open with a brief `### Done` (what was done), then the
suggestion categories (no archived-record section).

Item markers: `[open]` not yet addressed, `[acted]` already handled
(append a one-line note), `[needs-decision]` requires an owner decision.

When an `[open]` item is addressed or a `[needs-decision]` item is
decided, update the source report's marker (append a one-line note) — the
report file is the only place a status lives.

There is no roll-up file: the set of still-open items is derived from the
reports themselves, e.g.
`grep -rn "\[open\]|\[needs-decision\]" spec/report/`.

Traceability: markers carry no commit hashes. The resolution commit of an
item is found via `git blame` on the marker line, or `git log -S
"<marker phrase>" -- <report>` (pickaxe) for the commit that changed an
item's text.