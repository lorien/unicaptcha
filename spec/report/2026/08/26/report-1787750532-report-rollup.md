## Report on task: Drop the report roll-up (open.md)

### Spec/ADR amendments

- [open] The commit-hash traceability item (report-process) now has no
  roll-up home; its only surviving wording is in this report-process
  report.

### Future-task notes

- [acted] When adapting the report workflow in the future, prefer derived
  queries (`grep` over the markers) over maintained copies — a copy is a
  drift surface, not an index (encoded in report_tracking.md, spec sweep
  2026-08-26).

### Tooling/process

- [acted] Deleted `spec/report/open.md` (owner decision): the roll-up was
  a denormalized copy of the per-clause markers in the reports, cost a
  manual re-sync each session, and drifted in practice. Open items are
  now derived from the reports themselves —
  `grep -rn "\[open\]|\[needs-decision\]" spec/report/`.
- [acted] `report_tracking.md` now states there is no roll-up file and
  gives the grep command; the marker-lifecycle rule (flip the source
  report only) is unchanged.
- [acted] The historical "[acted] open.md created" entry in the
  report-process report is left as an accurate record; this reversal is
  documented by this report and its commit.