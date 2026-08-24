# ADR-0053: Adapter contract enforcement — ABC

**Status:** Accepted (settles the question left open by ADR-0052; amends ADR-0041, ADR-0042; `api_key` union per ADR-0063; report methods become bad/good pairs per ADR-0068; `referral` kwarg per ADR-0072; `endpoints` declaration per ADR-0073; `parse_submit_response` returns `SubmitAccepted` per ADR-0075; renamed 2026-08-24: `parse_task_result` → `parse_task_status`)
**Date:** 2026-08-23, amendment 2026-08-24

## Context

ADR-0052 named the contract class `BaseAdapter` but left its mechanism
pending: structural `typing.Protocol` vs nominal ABC.

Four facts decide it:

1. The Protocol hallmark — implementers import nothing — is void here.
   Adapter authors necessarily import unicaptcha types: custom kinds
   subclass `BaseChallenge`, and the `challenges` frozenset references
   our challenge classes. Nobody writes an adapter dependency-free.
2. Shared machinery is real, not speculative: key-masking `repr`/`str`
   is a contract (ADR-0014), not a per-author courtesy; all three
   providers share one request/response family (ADR-0001) wanting
   common lenient-parsing helpers (ADR-0040); `base_url` defaulting is
   uniform (README table).
3. The three shipped adapters need a common implementation base
   regardless. A public Protocol plus an internal base class would mean
   two definitions of the same contract, free to drift.
4. ABCs fail early and nominally: a missing method errors at the
   adapter author's instantiation; under a Protocol, untyped authors
   discover gaps as `AttributeError` mid-solve.

## Decision

- `BaseAdapter` is a public **abstract base class** (ABC) — the adapter
  SDK contract (ADR-0041).
- Mechanism rule: **Protocol to accept foreign objects; ABC for authored
    extensions.** The HTTP layer stays a Protocol (we accept existing
  httpx clients that will never subclass our base); adapters are
  extensions written against our contract.
- Registration check: the `CaptchaSolver` / `AsyncCaptchaSolver`
  constructor validates each element of `adapters=` with
  `isinstance(adapter, BaseAdapter)`; non-adapters (e.g. facades) raise
  `TypeError` — consistent with the wrong-object precedent of ADR-0045.
  Static rejection comes free from the nominal annotation.

### Member split

| Member | Kind |
|---|---|
| `provider`, `challenges` | abstract declarations (`provider` per ADR-0055) |
| `__init__(api_key: SecretStr \| str, base_url: str \| None = None, referral: bool \| str = True)` | concrete: wrap plain str into SecretStr (ADR-0063), store key; resolve `base_url or default_base_url`; store referral flag — the base embeds nothing, shipped adapters serialize their provider's affiliate field (ADR-0072) |
| `default_base_url: ClassVar[str]` | declared per provider (README table) |
| `endpoints: ClassVar[Endpoints]` | concrete JSON-family default; complete-set override only (ADR-0073) |
| `__repr__` / `__str__` | concrete, key masked (ADR-0014) |
| `build_payload`, `parse_submit_response`, `parse_task_status`, `parse_balance`, `map_provider_error` | abstract — the translation core |
| `report_bad_supported` / `build_report_bad` / `parse_report_bad` and good twins (`report_good_supported` / `build_report_good` / `parse_report_good`) | default unsupported (`False` / raise `UnsupportedCaptchaError`); shipped adapters override per the support matrix (ADR-0068) |
| `default_solve_config` | optional; default None |

## Rationale

- One public definition of the contract, shared by shipped and
  third-party adapters alike; no drift.
- The most safety-critical behavior (key masking) is inherited, not
  re-implemented per author.
- Nominal typing gives both static (annotation) and runtime
  (isinstance) enforcement with one name.

## Alternatives considered

- **Structural Protocol**: rejected; zero-import advantage void (fact
  1), untyped authors fail late (fact 4), shipped adapters still need
  an internal base (fact 3).
- **ABC plus runtime signature introspection**: rejected; overkill
  beyond isinstance.
- **Abstract `__init__` (each adapter stores its key)**: rejected;
  forfeits central enforcement of the masking contract.
