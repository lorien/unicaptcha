# Architecture

Complete technical design of unicaptcha. Every section links to the ADR that
records the decision's context and alternatives. This document is descriptive:
it states *what is* per the settled decisions; ADRs state *why*.

## 1. Layered design

```
+---------------------------------------------------------------+
| CaptchaSolver / AsyncCaptchaSolver             provider facades  |
| (registry + dispatch)                       (convenience)    |
+------------------------------+------------------------------+
                               |  both delegate to
+---------------------------------------------------------------+
| SolveEngine (internal)                                        |
| submit -> poll -> Result; retries, timeouts, events,          |
| abandoned-task registry, aux operations                       |
+---------------------------------------------------------------+
| Provider adapters (pure, no I/O)                              |
| challenge -> payload; response bytes -> typed Result          |
+---------------------------------------------------------------+
| HTTP layer (internal implementation behind a public Protocol) |
| httpx wiring, retry policy, per-request User-Agent, pool      |
+---------------------------------------------------------------+
```

- Universal clients and facades are **peers**: neither contains the other.
  Both delegate to the same internal SolveEngine (ADR-0007).
- The universal client holds a registry of provider adapters keyed by adapter
  `provider` (ADR-0055). `solve(challenge)` dispatches on the concrete challenge class:
  constructing the challenge is the provider choice (ADR-0005); kind-base
  challenges are routed by the optional `provider=` discriminator or uniform
  random choice among supporting adapters (ADR-0064).
- Facades (`TwoCaptchaClient` and async counterpart) know their provider
  statically; convenience methods construct challenges and delegate to the
  engine. Facade methods have full parameter parity with `solve()`
  (ADR-0051); facade constructors have full parity with `CaptchaSolver`
  except `adapters` — `api_key`, `base_url` (provider mirror override),
  and every client kwarg (ADR-0061).
- Adapters are pure translation units: challenge -> JSON payload, response
  bytes -> typed objects, provider error -> ErrorKind. No I/O, no state
  (ADR-0041).
- The HTTP layer is the **sole injection seam** for network resources. A
  caller-supplied httpx client is injected here, never mutated, and never
  closed by us (ADR-0024, ADR-0049).

### Ownership rules

- HTTP layer constructed by the library (from `HttpClientConfig` or defaults):
  library owns it; `close()` closes it.
- HTTP layer injected by the caller (httpx client instance): caller retains
  ownership; our `close()` never closes it.
- Passing both `http=HttpClientConfig(...)` and an injected httpx client is
  rejected with `InvalidConfigError` (ADR-0049).

### Provider identification

Each adapter declares `provider: ClassVar[str]` (e.g. `"twocaptcha"`). This
string is the single source of truth: registry key, `Result.provider`,
`TaskRef.provider`, `SolveEvent.provider`. Provider strings are public API.
Duplicate providers in one client are rejected at construction with
`ValueError` (ADR-0037).

### 2Captcha API flavor

2Captcha uses its **modern JSON API** (`createTask`/`getTaskResult`), not the
legacy `in.php`/`res.php` text protocol; all three providers then share one
request/response shape family (ADR-0001).

## 2. Challenge taxonomy

Two-level hierarchy, symmetric with solutions (ADR-0048, ADR-0006).

```
BaseChallenge (public abstract root; open for custom kinds)
+-- ImageChallenge          body: bytes | Path (normalized to bytes; ADR-0065)
+-- TextChallenge           text: str
+-- RecaptchaV2Challenge    sitekey: str; pageurl: str; invisible: bool
+-- RecaptchaV3Challenge    sitekey: str; pageurl: str; action: str|None; min_score: ...
+-- HCaptchaChallenge       sitekey: str; pageurl: str
```

- Kind bases are public, **instantiable** (ADR-0064), carry the
  **universal fields** (defined once), and link each kind to its
  solution type for precise static typing. A kind-base instance plus
  routing is a complete universal-fields-only solve request;
  solutions keep their non-instantiable rule (ADR-0035, ADR-0056).
- Provider subclasses (`TwoCaptchaRecaptchaV2Challenge`, ...) inherit the
  universal fields and add only provider-specific extras (ADR-0031).
- All challenges are **frozen dataclasses** with `__post_init__` validation
  raising `InvalidChallengeError` (ADR-0006, as amended by ADR-0041's dropping
  of pydantic).
- Dispatch in the universal client keys on the **concrete class**; the adapter
  contract lists concrete classes (ADR-0048). Kind-base instances are routed
  by `solve(provider=...)` or uniform random choice among supporting
  adapters, then upcast to the concrete class before `build_payload`
  (ADR-0064).
- Custom adapters may subclass `BaseChallenge` directly to introduce novel
  kinds; per-kind timing defaults then come from the adapter's declaration
  with generic fallback (ADR-0041).
- Image input is `bytes | Path`, Path normalized to bytes at
  construction (`InvalidChallengeError` chained from the OSError on
  read failure); the library base64-encodes internally (ADR-0025 as
  amended by ADR-0065). Text challenges take `str`.
- **Call style** (ADR-0066): kind-base fields are keyword-only except
  a kind's single payload field (`ImageChallenge(Path("..."))`,
  `TextChallenge("2+2?")`); multi-field kinds require keywords
  (`RecaptchaV2Challenge(sitekey=..., pageurl=...)`); provider extras
  and optional fields (`invisible=False`, `proxy=...`,
  `numeric=True`) are keyword-only. Kills the same-typed-string swap
  hazard and the non-default-after-default inheritance wart.

## 3. Solution taxonomy

```
BaseSolution (public abstract root; open for custom kinds; ADR-0056)
+-- ImageSolution          text: str                  (abstract)
+-- TextSolution           text: str                  (abstract)
+-- RecaptchaV2Solution    token: str                 (abstract)
+-- RecaptchaV3Solution    token: str; score; action  (abstract)
+-- HCaptchaSolution       token: str                 (abstract)
```

- Bases contain only fields all three providers return for that kind
  (ADR-0035, ADR-0034).
- Provider subclasses add provider-specific extras (e.g. Anti-Captcha's
  `user_agent`, `resp_key` for reCAPTCHA v2); optional provider fields the
  service did not return are `None`, never present in the base.
- Bases **reject direct instantiation** (`TypeError` from `__post_init__` when
  `type(self) is Base`); adapters always construct provider subclasses.
- The universal path types results as `Result[<Kind>Solution]`; facades and
  the challenge->solution link allow statically precise subclasses.

## 4. Models and public types

All models are frozen dataclasses (slots where beneficial; slotscheck in CI)
living in `unicaptcha.types` and re-exported from the root (ADR-0036).

### Result[T]

| Field | Type | Notes |
|---|---|---|
| `solution` | `T` | non-optional; always populated on solve() returns (ADR-0008) |
| `task_id` | `int` | provider task id |
| `cost` | `Decimal \| None` | provider-reported cost, `Decimal(str(raw))`; None when unreported |
| `raw` | `bytes` | untouched HTTP response body; uniform with `error.raw_response` |
| `provider` | `str` | adapter provider string |
| `created_at` | `datetime` | task submission time, UTC-aware |
| `elapsed` | `timedelta` | submission -> ready |
| `task_ref` | `TaskRef` | convenience property built from provider + task_id |

### TaskRef

Public, constructible: `TaskRef(provider: str, task_id: int)`. Registry
entries are TaskRefs (with abandoned-at metadata available from the registry
API). Routing vehicle for all task-addressing operations (ADR-0045).

### TaskTicket[T]

Issued by `submit()` (ADR-0067): frozen dataclass, generic over the
solution type (bound via the challenge->solution link); `task_ref:
TaskRef`, `submitted_at: datetime` (UTC). Not user-constructible —
provenance is its value. Bridges to persistence via `.task_ref`.

### TaskStatus

Returned by single-shot status queries (ADR-0032, ADR-0050; surface per
ADR-0056 — non-generic, no submission metadata):

| Field | Type |
|---|---|
| `task_id` | `int` |
| `provider` | `str` |
| `status` | `TaskState` — enum: `PENDING \| READY \| UNSOLVABLE \| UNKNOWN` |
| `solution` | `BaseSolution \| None` | populated only when READY; narrow via isinstance |
| `cost` | `Decimal \| None` |
| `raw` | `bytes` | untouched response body |

`Result[T]` is the solve()-only return; TaskStatus never embeds it.

Provider-side outcomes are always returned values; exceptions on this method
are reserved for caller-side faults (wrong provider -> TypeError, client
closed -> ClientClosedError, transport -> NetworkError).

### SolveEvent

| Field | Type |
|---|---|
| `phase` | `submitted \| poll \| retry \| solved \| failed` |
| `provider` | `str` |
| `task_id` | `int \| None` | None only before submission completes |
| `elapsed` | `timedelta` | since solve() start |
| `attempt` | `int` | poll/retry count within phase |
| `detail` | `str \| None` | e.g. "connection reset", "503"; never credentials |
| `error_kind` | `ErrorKind \| None` | failure phase only |

Invariant: every solve ends in exactly one of `solved` or `failed`. Cancellation
is eventless (ADR-0016, ADR-0018).

### Proxy / ProxyKind

```python
class ProxyKind(Enum): HTTP, HTTPS, SOCKS4, SOCKS5

@dataclass(frozen=True)
class Proxy:
    kind: ProxyKind = HTTP
    host: str            # required, non-empty
    port: int            # required, 1..65535
    username: str | None = None
    password: str | None = None
```

Structured fields, not a URL string; no normalization machinery (ADR-0012,
ADR-0028). Placement: optional `proxy` field on proxy-capable challenges;
client-level default proxy applied only to proxy-capable challenges,
challenge field wins. CapMonster is entirely proxyless; its challenge classes
carry no proxy field.

### SecretStr

Hand-rolled (~30 lines), masking in repr/str; used for API keys
(ADR-0014). No pydantic dependency.

### repr policy

- Bytes fields render as `<8234 bytes>` stubs, never content.
- Solution tokens/solved text render as `***abcd` (last 4 chars).
- API keys fully masked.
- `str` mirrors `repr`. (ADR-0034)

## 5. Configuration

Three frozen, all-fields-None-able config types (ADR-0043):

```python
HttpClientConfig(timeout, max_connections, max_keepalive_connections)
SolveConfig(total_timeout, poll_interval)
RetryConfig(max_attempts, backoff_base, backoff_cap)
```

- `HttpClientConfig.timeout` is per-request: the float maps to
  `httpx.Timeout(timeout)`, limiting each stage (connect, read, write,
  pool) independently — distinct from `SolveConfig.total_timeout`, the
  whole-solve budget (ADR-0024).

- `None` means "unspecified", never a value. Explicit bad values
  (`total_timeout=0`, `poll_interval=-5`) raise `InvalidConfigError` at config
  construction; `None` is always valid (ADR-0042).
- Resolution chain, field-wise (per-call value -> client value -> per-kind
  default table -> generic fallback). A per-call config **inherits** unset
  fields from the client config; it never discards them.
- Concrete defaults live only in the engine's kind-default table
  (ADR-0030), extended by adapter declarations for custom kinds
  (ADR-0041).
- Identity scalars stay flat constructor kwargs: `name`, `user_agent`,
  `abandoned_registry_limit`.
- Event handler: `on_event` accepted at construction and per call; per-call
  replaces client-level all-or-nothing (ADR-0044). On sync clients,
  coroutine-function handlers are rejected at attachment with
  `InvalidConfigError`; an awaitable returned at runtime logs a WARNING and
  is discarded. On async clients, awaitable results are awaited inline.
- Facade convenience methods accept `solve=`, `retry=`, `on_event=` with
  identical semantics (ADR-0051).

## 6. Error hierarchy

```
UnicaptchaError                    kind: ErrorKind; raw_response: bytes
+-- NetworkError
+-- AuthenticationError
+-- InsufficientBalanceError
+-- UnsupportedCaptchaError        provider lacks the operation/kind (both sides, ADR-0057)
+-- InvalidChallengeError          client-side challenge validation
+-- SolveTimeoutError
+-- RateLimitError
+-- UnsolvableCaptchaError
+-- InvalidConfigError
+-- ClientClosedError
+-- ProviderError                  unclassified provider errors
```

- `ErrorKind` (11 values): NETWORK, AUTH, BALANCE, UNSUPPORTED,
  INVALID_CHALLENGE, TIMEOUT, RATE_LIMIT, UNSOLVABLE, CLOSED,
  INVALID_CONFIG, PROVIDER (ADR-0009).
- No `provider_code` attribute; the message travels via standard Exception
  machinery; `raw_response` preserves the verbatim provider bytes.
- No `SolveCancelledError` (ADR-0016); no `UnknownTaskError` (ADR-0050).
- Wrong-provider challenge or TaskRef passed to a client: `TypeError`,
  raised pre-flight, no network traffic (ADR-0045).
- HTTP 200 with unparseable body or wrong-shape JSON: `ProviderError` with
  `raw_response` preserved and the parse failure chained as `__cause__`
  (ADR-0040).
- Chaining discipline: every wrapped cause uses `raise ... from cause`.
  Event-handler exceptions propagate raw (ADR-0018).
- Principle: **status queries answer, operations raise** (ADR-0050).

## 7. Solve flow and behavior

```
solve(challenge, provider=None, solve=None, retry=None, on_event=None) -> Result[T]
    validate client open
    dispatch challenge -> adapter (universal) or direct (facade):
        concrete class -> its adapter (provider= must match if given, else TypeError)
        kind base + provider="name" -> that adapter (TypeError if unknown,
            UnsupportedCaptchaError if kind unsupported)
        kind base + provider=None -> uniform random choice among supporting
            adapters (ADR-0064); upcast to concrete class before build_payload
    submit phase:
        build payload (adapter, pure)
        POST createTask
          - pre-send failure (DNS, refused, TLS, connect-timeout): retry
          - received 500/503: retry
          - rate limit (429 / provider payload): retry, RateLimitError on exhaustion (ADR-0059)
          - read timeout, reset-after-send, 502/504: fail fast NetworkError
          - backoff: full jitter, base 1s, cap 30s, max 3 attempts
    poll phase:
         POST getTaskResult every poll_interval
           - transient failures tolerated, bounded by total_timeout
           - UNSOLVABLE response -> UnsolvableCaptchaError (no auto-resubmit)
           - UNKNOWN (task not found) -> ProviderError, fail fast (ADR-0058)
    terminal:
        READY -> Result[T] (emit "solved")
        budget exhausted -> SolveTimeoutError (emit "failed")
        any raised library error emits "failed" first, then raises
```

- `total_timeout` covers submit attempts + backoff + polling, starting at the
  `solve()` call (ADR-0010). Enforced internally via `asyncio.timeout()` on
  the async side, converted to `SolveTimeoutError` at our scope boundary
  only; external cancellation passes through untouched.
- Aux operations (`get_balance`, `report_bad_result`, `get_task_result`)
  use the **same** retry policy as submission (ADR-0011).
- Polling only; no webhooks (ADR-0015).

### Two-phase operations (ADR-0067)

`solve() = submit() + wait()`, exposed as separate calls on both tiers:

```python
ticket = solver.submit(challenge, provider=None, retry=None)   # -> TaskTicket[T]
result = solver.wait(ticket, timeout=None)                     # -> Result[T], raises on failure
status = solver.wait_ref(TaskRef(...), timeout=120)            # -> TaskStatus, answers (PENDING on budget out)
```

- `submit` routes exactly like `solve()` (ADR-0064); bounded by the
  retry policy only.
- `wait`: operation semantics — `Result[T]` typed, raises
  (`UnsolvableCaptchaError`, UNKNOWN -> `ProviderError` per ADR-0058,
  `SolveTimeoutError`); clock starts at the call, default = per-kind
  `total_timeout` (ADR-0030) via the merge chain.
- `wait_ref`: query semantics — polls until terminal or budget out
  (returns PENDING `TaskStatus` on exhaustion).
- `get_task_result` unchanged: single-shot (ADR-0050).
- Events: `submitted` at submit; `solved`/`failed` at wait's terminal
  state; never-waited tickets eventless (ADR-0018 as amended).
  Deferral is not abandonment (ADR-0038 as amended): the registry
  records only cancelled/orphaned waits. Billing caveat: solved but
  uncollected tasks are billed by the provider.


### Auxiliary operations

| Operation | Universal client | Facade |
|---|---|---|
| `get_balance(provider)` | provider discriminator: instance / class / provider string; returns `Decimal` USD | implicit provider |
| `get_task_result(task)` | `TaskRef` | `int \| TaskRef` |
| `report_bad_result(task)` | `TaskRef` | `TaskRef \| int` |
| `report_good_result(task)` | `TaskRef` | `TaskRef \| int` (ADR-0068; returns bool, feeds worker quality routing where supported) |
| `abandoned_tasks()` | snapshot `tuple[TaskRef, ...]` | same |

Report-bad coverage differs per provider and captcha kind; adapters enforce
the support matrix pre-flight and raise `UnsupportedCaptchaError` where the
provider lacks coverage (ADR-0057). Balance is pinned to USD `Decimal`
(ADR-0040).

### Cancellation (ADR-0016)

- `asyncio.CancelledError` propagates untouched; never swallowed, never
  substituted.
- The abandoned `task_id` lands in the abandoned-task registry via
  synchronous bookkeeping (no awaits during cancellation unwinding).
- Billing caveat documented: abandoned tasks may still be billed; reclaim
  via `get_task_result` later.
- Sync side: `KeyboardInterrupt` propagates naturally.

### Client lifecycle (ADR-0033)

- `close()` / `aclose()`: idempotent; context managers on all clients.
- Eager httpx construction at `__init__`; no lazy init.
- Use after close: any operation raises `ClientClosedError`.
- Sync close with in-flight solves: a `threading.Event` shutdown flag wakes
  blocked solves at their next checkpoint (`Event.wait(timeout=...)` replaces
  sleeps). Close latency is at most one in-flight HTTP round trip.
  Interrupted solves raise `ClientClosedError`; their task ids enter the
  registry.
- Async close: cancels in-flight tasks (clean CancelledError propagation),
  then closes connections.
- The abandoned-task registry **survives** close; `abandoned_tasks()` remains
  readable afterward (ADR-0038).

### Abandoned-task registry (ADR-0038)

- Typed entries (TaskRef + abandoned-at metadata); thread-safe append-only
  storage; `abandoned_tasks()` returns a snapshot tuple, never a live list.
- Bounded: default cap 1000, one WARNING log per eviction, cap configurable
  client-side (`abandoned_registry_limit`), `None` = unbounded.
- Per-client, best-effort, **advisory** (ADR-0060): entries removed when a
  same-client `get_task_result` reaches a terminal state; cleared never
  (survives close); cross-client reclaim leaves stale entries (harmless,
  bounded).
- No automatic reclaim loop; the caller drives reclamation:
  snapshot `abandoned_tasks()` -> new client with the same adapters ->
  `get_task_result(ref)` per entry -> terminal states are answers
  (ADR-0050, ADR-0056); persist TaskRefs to survive restarts.

## 8. Logging and events

- One flat logger: `logging.getLogger("unicaptcha")`. No per-instance or
  hierarchical logger names (ADR-0018; hierarchical names deferred).
- Client identity, when needed, travels as context: optional client `name`
  in messages / `extra` fields, never as logger names.
- Handlers are called inline: awaited-if-awaitable (async), direct call in
  the solving thread (sync). Handlers must be fast; a slow handler delays
  polling.

| Level | Content | Never contains |
|---|---|---|
| DEBUG | HTTP method/URL/status, raw response bytes, poll iterations, retry decisions, unknown response fields | API keys |
| INFO | task submitted (provider, task_id), task solved (task_id, elapsed), client open/close | solution tokens, keys, bodies |
| WARNING | retryable failures, proxy ignored on proxyless kind, registry eviction, awaitable handler result discarded | |
| ERROR | nothing; errors are exceptions, callers decide logging | |

Solution tokens never appear at any level. Key scrubbing is targeted (keys
occupy known payload positions; we construct all payloads).

## 9. Package layout, imports, boundary

```
unicaptcha/
    __init__.py        # curated re-exports: clients, errors, ErrorKind,
                       # Result, TaskStatus, SolveEvent, TaskRef, SecretStr,
                       # configs, Proxy/ProxyKind, challenge/solution kind bases
    _version.py        # single version source (pyproject reads it)
     client.py          # CaptchaSolver / AsyncCaptchaSolver
    errors.py          # hierarchy + ErrorKind
    events.py          # SolveEvent
    types.py           # public model vocabulary (Result, TaskStatus, TaskRef,
                       # Proxy, SecretStr, configs, kind bases re-exported)
    solutions/         # abstract solution kind bases
    providers/
        twocaptcha/    # challenges, solutions, adapter, facades
        anticaptcha/
        capmonster/
    _internal/         # engine, http layer implementation, clock, scrubbing
```

- Import model: **eager**. `import unicaptcha` pre-loads provider packages;
  root exposes core vocabulary; provider classes require explicit subpackage
  imports (`from unicaptcha.providers.twocaptcha import ...`).
- Public surface: root + provider packages + the adapter SDK contract
  (`BaseChallenge`, `BaseAdapter` ABC, registration). Everything under
  `_internal/` plus module privates are implementation details. The HTTP
  layer is exposed as a public **Protocol** (what may be injected), while its
  implementation stays internal (ADR-0041).
- Naming: universal `CaptchaSolver` / `AsyncCaptchaSolver`; facades
  `<Provider>Client` / `Async<Provider>Client`; challenges
  `<Provider><Kind>Challenge`; solutions `<Provider><Kind>Solution`
  (ADR-0036).
- Facade methods: `solve_image`, `solve_text`, `solve_recaptcha_v2`,
  `solve_recaptcha_v3`, `solve_hcaptcha`; aux ops named identically on both
  tiers (`get_balance`, `get_task_result`, `report_bad_result`).

### Adapter SDK (ADR-0041)

```python
class MyServiceAdapter(BaseAdapter):
    provider: ClassVar[str] = "myservice"
    challenges: ClassVar[frozenset[type[BaseChallenge]]]
    default_solve_config: ClassVar[...]        # per-kind timing defaults; optional

    def __init__(self, api_key: SecretStr | str, base_url: str | None = None): ...
    def build_payload(self, challenge) -> dict[str, Any]: ...
    def parse_submit_response(self, raw: bytes) -> int: ...
    def parse_task_result(self, raw: bytes) -> ParsedTask: ...   # pending|ready|unsolvable|unknown (ADR-0058)
    def parse_balance(self, raw: bytes) -> Decimal: ...
    def report_bad_supported(self, challenge_type) -> bool: ...
    def build_report_bad(self, task: TaskRef) -> dict[str, Any]: ...
    def parse_report_bad(self, raw: bytes) -> bool: ...
    def report_good_supported(self, challenge_type) -> bool: ...   # ADR-0068
    def build_report_good(self, task: TaskRef) -> dict[str, Any]: ...
    def parse_report_good(self, raw: bytes) -> bool: ...
    def map_provider_error(self, raw: bytes) -> ErrorKind and message: ...
```

- Registration: `CaptchaSolver(adapters=[MyServiceAdapter(...)])`.
  Non-adapter objects (e.g. facades) raise `TypeError` at construction
  (ADR-0053).
- `BaseAdapter` is a public ABC (ADR-0053): `provider` (ADR-0055),
  `challenges`, and
  the translation methods are abstract; `__init__` (api_key storage,
  `base_url` defaulting), key-masking `repr` (ADR-0014), and the
  report default-unsupported pairs (bad + good, ADR-0068) are
  concrete.
- Third-party facades: author-written composition of a universal client,
  following the documented pattern; no generation machinery (rejected:
  kills static typing).
- The test suite contains a **reference third-party adapter** ("myservice")
  implemented against public API only; CI enforces it never imports
  `_internal` (ADR-0046).

## 10. Infrastructure

- **Python**: 3.11+ floor; also the async-side requirement for
  `asyncio.timeout()` internals (ADR-0004).
- **Typing**: fully annotated, `py.typed`, mypy strict + pyright strict in
  CI.
- **Build**: hatchling; version single-sourced from
  `unicaptcha/_version.py`; `unicaptcha.__version__` exposed (ADR-0046).
- **Lint/format**: ruff (E, W, F, I, B, UP, SIM, RUF; target py311; 88
  cols). ANN rejected (type checkers cover it).
- **Tests**: pytest + pytest-asyncio (strict mode) + respx (HTTP mocked at
  transport level; no real API calls). Optional integration suite marked
  `integration`, deselected by default (`-m 'not integration'`), API keys
  via environment. Reference third-party adapter in tests. Injectable
  clock/sleep seam in the engine enables deterministic, instant tests of
  timeouts, backoff, and poll cadence.
- **CI (GitHub Actions)**: lint + both type checkers + tests on matrix
  Python 3.11/3.12/3.13/3.14 x {Linux, macOS}, blocking; 3.14t
  (free-threaded) x Linux informational (`continue-on-error`), promotable.
  Coverage informational only. Release consistency checks: tag ==
  pyproject version == matching CHANGELOG section (ADR-0021, ADR-0022).
- **Dependencies**: runtime `httpx>=0.27` only. Dev group: ruff, mypy,
  pyright, pytest, pytest-asyncio, respx, pytest-cov, slotscheck
  (ADR-0019). No HTTP/2; TLS customization via httpx client injection only.
- **Versioning/licensing**: SemVer from 0.1.0, static bump; manual
  Keep-a-Changelog; MIT.
