## Report on task: Adapter golden-payload tests

### Task (archived from plan.md)

```
## Adapter golden-payload tests

Status: done

respx transport-level tests for all five adapters (four providers +
reference "myservice"):

- Exact outgoing URL + JSON payload assertions per kind × provider
  against the ADR-0076 field tables (universal→wire mapping, provider
  extras, proxy/worker-context serialization, referral embedding).
- Response parsing: `SubmitAccepted` (incl. `instant_answer`),
  `ParsedTask` state machine (pending/ready/unsolvable/unknown), balance,
  report bad/good; malformed/wrong-shape bodies → `ProviderError` with
  `raw_response` and chained cause.
- Error mapping per provider (rate-limit, busy, auth, balance) and the
  support matrix (report `*_supported`, unsupported kinds raise
  `UnsupportedChallengeError`).

References: ADR-0019, ADR-0040, ADR-0058, ADR-0068, ADR-0072, ADR-0075.
```

### Done

- Added `tests/test_golden_payloads.py` — 119 transport-level tests
  driving the real `Solver`/`AsyncSolver` over respx (no adapter-level
  shortcuts), locking the wire contract for all five adapters.
- Golden payload matrix: 36 cases (one per kind × provider; 2Captcha 9,
  Anti-Captcha 9, CapMonster 8, Capsolver 8, myservice 2), each asserting
  POST method, exact `base_url + /createTask` URL, and the full JSON body
  (envelope + `task` type + wire-mapped fields) per the ADR-0076 tables.
- Referral embedding (ADR-0072): `softId` for 2Captcha/Anti-Captcha/
  CapMonster when `referral="4704"`; myservice string→softId; Capsolver
  referral inert; `referral=False` and default-`True` embed nothing.
- Proxy/worker-context serialization (ADR-0012/0069): 2Captcha v2
  proxy+UA+cookies (header-string), Anti-Captcha IP-only proxy (hostname
  rejected pre-flight), CapMonster proxyless (no proxy fields anywhere),
  Capsolver proxy with credentials.
- Provider extras → wire names (ADR-0076): 2Captcha image extras +
  envelope `languagePool`, v3 enterprise/action/minScore/apiDomain,
  Anti-Captcha task `languagePool`/`lang`, CapMonster v2 enterprise +
  Turnstile extras, Capsolver Turnstile `metadata`.
- Response parsing at transport level: submit→poll→READY with
  `getTaskResult` URL/payload asserted; submit-ready fast path with no
  poll request (ADR-0075); NO_SOLUTION→`NoSolutionError`; UNKNOWN→
  `ProviderError` fail-fast; malformed JSON and wrong-shape bodies→
  `ProviderError` with `raw_response` preserved (chained `ValueError`
  cause on parse failure); empty solution→`EmptySolutionError`;
  `get_balance`, `report_bad`/`report_good` round trips; `wait_ref`
  poll payload.
- Error mapping (ADR-0009): per-provider submit error codes→public
  exceptions (auth/balance/busy), HTTP 429→`RateLimitError` with retry
  count, balance errors→`InsufficientBalanceError`.
- Support matrix (ADR-0057/0068): text kind unsupported on
  CapMonster/Capsolver raises `UnsupportedChallengeError`; report bad/good
  unsupported on Anti-Captcha/CapMonster/Capsolver.
- Async tier spot checks: async golden submit matrix (all 36 cases),
  async instant fast path, async error mapping.

### Spec/ADR amendments

- None needed: the wire payloads produced by all five adapters match the
  ADR-0076 field tables exactly; no adapter or doc changes were required.

### Future-task notes

- Deferred item 22 (provider-fidelity verification method) remains open:
  these golden payloads are hand-authored from the architecture tables,
  not regenerated from vendor SDKs. The suite is a static fixture set; the
  "regenerated from vendor sources" algorithm is still future work.

### Tooling/process

- [open] `_fast_time()`/`_fast_retry()` helpers are duplicated across the
  per-provider test files and this suite, while `conftest.py` already
  provides `fast_time`/`fast_retry` fixtures used by the reference-adapter
  tests. Consolidating the duplicated helpers onto those fixtures would
  remove ~4 copies.
- [open] Payload-only assertions use `submit()` (no poll noise), while
  solve-path tests require the fast time/retry configs; default backoff
  (1/30 s) and poll delay (5 s) would make solve-based tests real-time.
  A note in `testing.md` about always passing fast configs for
  engine-round-trip tests could help future authors.