# Task 5: Challenge kind bases

Status: new

Implement the `challenge/` package:

- `BaseChallenge` (public abstract root) and the nine instantiable kind
  bases: `ImageChallenge`, `TextChallenge`, `RecaptchaV2Challenge`,
  `RecaptchaV3Challenge`, `HCaptchaChallenge`, `FunCaptchaChallenge`,
  `GeeTestV3Challenge`, `GeeTestV4Challenge`, `TurnstileChallenge`.
- Frozen dataclasses with `__post_init__` validation raising
  `InvalidChallengeError`; keyword-only call style (single payload field
  positional; multi-field and extras keyword-only).
- Image `body: bytes | Path` normalized to bytes (OSError chained);
  universal fields and per-kind solution-type link.
- Enterprise/kind flags (`is_enterprise`, `data_s`, `api_domain`,
  `is_invisible`, `rqdata`, `action`, `c_data`, `chl_page_data`) and the
  worker-context/proxy placement rules.
- Provider subclass pattern documented (universal fields inherited,
  provider extras per ADR-0076).

References: ADR-0006, ADR-0025, ADR-0031, ADR-0048, ADR-0064, ADR-0065,
ADR-0066, ADR-0069, ADR-0070, ADR-0074, ADR-0076, ADR-0012.

Note: task 5 and task 6 (solution kind bases) are one unit — the
challenge->solution type link and the symmetric taxonomy are inseparable;
executed folded (see Done below).

## Done

- Implemented `unicaptcha/challenge/`: `BaseChallenge` (abstract,
  non-instantiable root, open for custom kinds) and the nine instantiable
  kind bases — `ImageChallenge`, `TextChallenge`, `RecaptchaV2Challenge`,
  `RecaptchaV3Challenge`, `HCaptchaChallenge`, `FunCaptchaChallenge`,
  `GeeTestV3Challenge`, `GeeTestV4Challenge`, `TurnstileChallenge` — one
  file per kind (ADR-0036/0048).
- All kind bases: `frozen=True, slots=True`, field-level `kw_only=True` on
  multi-field kinds (ADR-0066 call style; single-payload `body`/`text`
  positional-or-keyword), minimal `__post_init__` validation (non-empty
  required strings -> `InvalidChallengeError`), `solution_type` ClassVar
  linking each kind to its solution base (task 6, folded in).
- Enterprise/kind flags: `is_enterprise`/`data_s`/`api_domain`
  (reCAPTCHA v2/v3, ADR-0070), `is_invisible`/`rqdata` (hCaptcha),
  `action`/`c_data`/`chl_page_data` (Turnstile, ADR-0074).
- `ImageChallenge.body: bytes | Path` normalized to bytes in
  `__post_init__` (Path read; OSError chained as `InvalidChallengeError`,
  ADR-0065); repr stubs bytes (ADR-0034).
- No `proxy`/`user_agent`/`cookies` on kind bases — those are
  provider-subclass extras per ADR-0012/0069/0076; documented.
- `challenge/__init__.py` re-exports all kind bases; root re-exports them.
- Tests: abstract-root guard, per-kind keyword-required enforcement,
  validation, flag defaults, single-payload positional style, image
  Path/bytes + chained OSError, repr bytes stub, `solution_type` link
  table, fake provider subclass proving the kw_only inheritance-wart
  elimination (ADR-0066).
- Full suite green (ruff, mypy strict, pyright strict, slotscheck, pytest
  124 passing). No hard-coded credentials.