# Vendor source checkouts

The gitignored `var/vendor/` tree holds upstream source checkouts for
research and reference. Nothing here is committed.

## Layout

- `var/vendor/repo/<repo-name>` — official SDK / client clones, one per
  provider (e.g. `var/vendor/repo/2captcha-python`).
- Future space for analysis artifacts (e.g. `var/vendor/analysis-*.md`).

## Purpose

- Cross-check adapter integrity against official SDK behavior (task-type
  strings, field wire names, error-code tables).
- Reference for wire-contract and provider-fidelity work.
- Consult these when modeling behavior off a vendor SDK, or when asked to
  do vendor research.

## Notes

- Clones are upstream and shallow (`--depth 1`); they may be stale.
- Treat them as read-only references — never commit or edit upstream code.
