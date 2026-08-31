## Report on task: Kind timing defaults — text budget

Closed the plan.md record of the same name (text kind's 30 s default
budget expired twice on real 2Captcha workers during the 2026-08-28 live
smoke).

### Done

- Split the image/text row in the ADR-0030 timing table. Text now has its
  own row: `poll_delay 5 s / poll_interval 2 s / total_timeout 120 s`
  (`unicaptcha/_internal/defaults.py` `_KIND_TIMINGS`). Image keeps
  `5/2/30`.
- 120 s anchored to 2Captcha's own SDK `defaultTimeout=120`; no new live
  measurement run (owner decision: ratify from vendor default + smoke
  evidence).
- Test: `tests/test_engine_timing.py` `test_per_kind_default_rows` now
  asserts the text row (`TextChallenge` → 120/2/5) — previously text was
  only implicitly covered via the image row.
- Docs amended: ADR-0030 (status line, table header/rows, new Text-row
  bullet, context + rationale), ADR-0067 budget note (image 30 s, text
  120 s), `spec/docs/index.md` ADR-0030 amendment note.
- CHANGELOG Unreleased **Fixed** entry for the new text default.

### Verification

`uv run ruff check .` / `ruff format --check` / `mypy unicaptcha` /
`pyright` / `slotscheck unicaptcha` / `uv run pytest` — all pass
(456 passed, 7 integration deselected).

### Future-task notes

- The plan record "Example verification: execute, not just compile"
  (Priority 2) remains the next actionable item; the text example would
  be one of its canned-response cases.
- No live latency data was captured for text solves; if the queue-bound
  variance is ever questioned again, 2Captcha returns `createTime`/
  `endTime` in task results, so real durations are cheap to record.