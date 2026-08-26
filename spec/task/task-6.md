# Task 6: Solution kind bases

Status: new

Implement the `solution/` package:

- `BaseSolution` (public abstract root) and the nine abstract kind bases:
  `ImageSolution`, `TextSolution`, `RecaptchaV2Solution`,
  `RecaptchaV3Solution`, `HCaptchaSolution`, `FunCaptchaSolution`,
  `GeeTestV3Solution`, `GeeTestV4Solution`, `TurnstileSolution`.
- Non-instantiable rule: bases reject direct construction (`TypeError`);
  adapters always construct provider subclasses.
- Base fields contain only what all providers return for the kind;
  provider extras land on subclasses (`None` when absent).
- repr policy on solution values.

References: ADR-0034, ADR-0035, ADR-0056, ADR-0070, ADR-0074.

## Done

- Implemented `unicaptcha/solution/` alongside task 5 (folded execution,
  owner-approved): the abstract `BaseSolution` root (already present from
  task 2) plus the nine non-instantiable kind bases — `ImageSolution`,
  `TextSolution`, `RecaptchaV2Solution`, `RecaptchaV3Solution`,
  `HCaptchaSolution`, `FunCaptchaSolution`, `GeeTestV3Solution`,
  `GeeTestV4Solution`, `TurnstileSolution`.
- Non-instantiable rule enforced per kind via `__post_init__`
  `guard_abstract(self, <Kind>)` (shared helper in
  `_internal/taxonomy.py`); the root guard stays on `BaseSolution`.
- Base fields hold only universal values (token/text for token kinds;
  `score`/`action` optional on V3; GeeTest three-/five-part answers).
- repr policy: custom `__repr__` per kind truncates answer strings via
  `truncate_token` (ADR-0034); `__str__` mirrors `repr`.
- `solution/__init__.py` re-exports root + kinds; root re-exports them.
- Tests: each kind base rejects direct construction (TypeError), concrete
  subclasses instantiate, repr truncation, str==repr.
- Full suite green. No hard-coded credentials.