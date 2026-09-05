## Report on task: Report commit-hash traceability

### Task (archived from plan.md)

Status: done

Whether session/task reports should cite commit hashes for traceability
(undecided; currently reports cite task names and dates only).

### Done

Decision (owner-selected, option 1): keep git as the source of truth for
hashes; do not embed them in reports as a rule.

- `spec/skills/report_tracking.md` Traceability note clarified:
  - Markers (`[open]` / `[acted]` / `[needs-decision]`) never carry
    commit hashes.
  - A report is committed atomically with the work it documents, so it
    never cites its own implementation hash; own-work traceability stays
    via `git blame` on the marker line or `git log -S "<phrase>" --
    <report>` (pickaxe).
  - Reports may cite the commit hashes of *already-existing* prior work
    in prose (e.g. "commit `2c31a47`") when referencing another task's
    implementation — formalizing the practice already used in earlier
    reports.

### Spec/ADR amendments

- `spec/skills/report_tracking.md`: Traceability note rewritten.

### Future-task notes

None.

### Tooling/process

The reason own-work hashes are out: the report is written and committed
in the same commit as the code it documents, so the hash is unknowable at
write time. The alternative (separate follow-up commit per task, as the
soft_id archive did: `f61ef09` → `df5b0cb`) was not chosen — it adds a
commit per task for marginal benefit.