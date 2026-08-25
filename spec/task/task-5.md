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