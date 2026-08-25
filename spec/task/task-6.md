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