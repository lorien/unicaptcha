# Vendor source checkouts

The gitignored `var/vendor/` tree holds upstream source checkouts for
research and reference. Nothing here is committed.

## Layout

- `var/vendor/repo/<repo-name>` — official SDK / client clones, one per
  provider (e.g. `var/vendor/repo/2captcha-python`).
- `var/vendor/<repo-name>-analysis.md` — one knowledge base per provider SDK:
  layout, architecture, wire protocol, task-type/field tables, polling and
  timeouts, proxy handling, error model, and fidelity gotchas. Written to be
  loaded quickly to reload the state of the vendor's source without re-reading
  the clone.

## Purpose

- Cross-check adapter integrity against official SDK behavior (task-type
  strings, field wire names, error-code tables).
- Reference for wire-contract and provider-fidelity work.
- Consult these when modeling behavior off a vendor SDK, or when asked to
  do vendor research.

## Notes

- Clones are upstream and shallow (`--depth 1`); they may be stale.
- Treat them as read-only references — never commit or edit upstream code.
