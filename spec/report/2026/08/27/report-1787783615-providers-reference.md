## Report on task: supported providers reference

### Spec/ADR amendments

- [acted] Added `spec/ref/providers.md` — the four v1 providers
  (ADR-0001/0071) with kind, official website, official Python repo, and
  API documentation URL, listed one property per line as plain prose (no
  tables, no markdown links per owner; mirrors section removed on owner
  request — RuCaptcha stays documented in ADR-0071 only). Linked from the
  `spec/ref/index.md` documents table.
- [open] `providers.md` records the official repo per provider. CapMonster
  Cloud's SDK moved from `ZennoLab/capmonstercloud-client-python` to
  `CapMonsterCloud/capmonster-python-captcha-solver` (verified via git
  origin + README + analysis note); confirm the moved URL stays canonical
  when the CapMonster adapter (task 13) lands.

### Future-task notes

- Tasks 12–14 (Anti-Captcha, CapMonster, Capsolver adapters) can cross-check
  their vendor analysis docs against this reference list for repo/website
  URLs.

### Tooling/process

- Provider/repo facts were sourced from the vendored checkouts' `.git/config`
  origins and setup/pyproject metadata plus `var/analysis-*.md` — faster and
  more authoritative than web browsing; the same source set should back the
  future provider reference additions.