# Architecture

Complete technical design of unicaptcha. Every section links to the ADR that
records the decision's context and alternatives. This document is descriptive:
it states *what is* per the settled decisions; ADRs state *why*.

## 1. Layered design

```
+---------------------------------------------------------------+
| Solver / AsyncSolver             provider facades  |
| (registry + dispatch)                       (convenience)    |
+------------------------------+------------------------------+
                               |  both delegate to
+---------------------------------------------------------------+
| TaskEngine (internal)                                        |
| submit -> poll -> TaskResult; retries, timeouts, events,          |
| abandoned-task registry, aux operations                       |
+---------------------------------------------------------------+
| Provider adapters (pure, no I/O)                              |
| challenge -> payload; response bytes -> typed TaskResult          |
+---------------------------------------------------------------+
| HTTP layer (internal implementation behind a public Protocol) |
| httpx wiring, retry policy, per-request User-Agent, pool      |
+---------------------------------------------------------------+
```

- Universal clients and facades are **peers**: neither contains the other.
  Both delegate to the same internal TaskEngine (ADR-0007).
- The universal client holds a registry of provider adapters keyed by adapter
  `provider` (ADR-0055). `solve(challenge)` dispatches on the concrete challenge class:
  constructing the challenge is the provider choice (ADR-0005); kind-base
  challenges are routed by the optional `provider=` discriminator or uniform
  random choice among supporting adapters (ADR-0064).
- Facades (`TwoCaptchaClient` and async counterpart) know their provider
  statically; convenience methods construct challenges and delegate to the
  engine. Facade methods have full parameter parity with `solve()`
  (ADR-0051); facade constructors have full parity with `Solver`
  except `adapters` — `api_key`, `base_url` (provider mirror override),
  and every client kwarg (ADR-0061).
- Adapters are pure translation units: challenge -> JSON payload, response
  bytes -> typed objects, provider error -> ErrorKind. No I/O, no state
  (ADR-0041).
- The HTTP layer is the **sole injection seam** for network resources. A
  caller-supplied httpx client is injected here, never mutated, and never
  closed by us (ADR-0024, ADR-0049). Request URLs are built by the engine:
  `adapter.base_url + adapter.endpoints.<operation>` (ADR-0073).

### Ownership rules

- HTTP layer constructed by the library (from `NetworkConfig` or defaults):
  library owns it; `close()` closes it.
- HTTP layer injected by the caller (httpx client instance): caller retains
  ownership; our `close()` never closes it.
- Passing both `network=NetworkConfig(...)` and an injected httpx client is
  rejected with `InvalidConfigError` (ADR-0049).

### Provider identification

Each adapter declares `provider: ClassVar[str]` (e.g. `"twocaptcha"`). This
string is the single source of truth: registry key, `TaskResult.provider`,
`TaskRef.provider`, `TaskEvent.provider`. Provider strings are public API.
Duplicate providers in one client are rejected at construction with
`ValueError` (ADR-0037).

### 2Captcha API flavor

2Captcha uses its **modern JSON API** (`createTask`/`getTaskResult`), not the
legacy `in.php`/`res.php` text protocol; all four providers then share one
request/response shape family (ADR-0001).

## 2. Challenge taxonomy

Two-level hierarchy, symmetric with solutions (ADR-0048, ADR-0006).

```
BaseChallenge (public abstract root; open for custom kinds)
+-- ImageChallenge          body: bytes | Path (normalized to bytes; ADR-0065)
+-- TextChallenge           text: str
+-- RecaptchaV2Challenge    sitekey: str; pageurl: str; invisible: bool
|                           enterprise flags: is_enterprise, data_s, api_domain (ADR-0070)
+-- RecaptchaV3Challenge    sitekey: str; pageurl: str; action: str|None; min_score: ...
|                           enterprise flags: is_enterprise, data_s, api_domain (ADR-0070)
+-- HCaptchaChallenge       sitekey: str; pageurl: str
|                           flags: is_invisible, rqdata (ADR-0070)
+-- FunCaptchaChallenge     public_key: str; pageurl: str (ADR-0070)
+-- GeeTestV3Challenge      gt_key: str; challenge: str; pageurl: str (ADR-0070)
+-- GeeTestV4Challenge      captcha_id: str; pageurl: str (ADR-0070)
+-- TurnstileChallenge      sitekey: str; pageurl: str (ADR-0074)
|                           flags: action, c_data, chl_page_data (ADR-0074)
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

### Provider-specific challenge field surface (ADR-0076, closes deferred item 2)

Concrete classes add provider extras beyond the universal kind-base
fields. Convention: `sitekey`→`websiteKey` and `pageurl`→`websiteURL`
unless the wire name differs (noted per row). Provider extras type as
primitives in v1 (`str | None`, `int | None`, `bool`); enum promotion
deferred (StrEnum later). Worker-context (`user_agent`/`cookies`,
ADR-0069) and `proxy` (ADR-0012) ride as keyword-only fields where the
provider API accepts them; CapMonster challenges carry **no** proxy
field (proxyless, ADR-0012).

#### 2Captcha (`twocaptcha`; all nine kinds)

| Kind | Concrete class | Provider extras → wire | Proxy / worker |
|---|---|---|---|
| image | `TwoCaptchaImageChallenge` | `phrase→phrase`, `case→case`, `numeric→numeric` (0-4), `math→math`, `min_len→min_len`, `max_len→max_len`, `lang→lang`, `comment→comment` | proxy opt. |
| text | `TwoCaptchaTextChallenge` | `lang→lang` | — |
| reCAPTCHA v2 | `TwoCaptchaRecaptchaV2Challenge` | `is_enterprise→RecaptchaV2EnterpriseTask` (+`enterprisePayload`), `data_s→recaptchaDataSValue`, `api_domain→apiDomain` | proxy opt.; UA + cookies |
| reCAPTCHA v3 | `TwoCaptchaRecaptchaV3Challenge` | `action→pageAction`, `min_score→minScore`, `is_enterprise→RecaptchaV3EnterpriseTask` (+`enterprisePayload`), `api_domain→apiDomain` | proxy opt.; UA + cookies |
| hCaptcha | `TwoCaptchaHCaptchaChallenge` | `rqdata→enterprisePayload` | proxy opt.; UA + cookies |
| FunCaptcha | `TwoCaptchaFunCaptchaChallenge` | `public_key→websitePublicKey`, `data→data` (blob), `service_url→funcaptchaApiJSSubdomain` | proxy opt.; UA |
| GeeTest v3 | `TwoCaptchaGeeTestV3Challenge` | `gt_key→gt`, `challenge→challenge`, `api_server→geetestApiServerSubdomain` | proxy opt.; UA |
| GeeTest v4 | `TwoCaptchaGeeTestV4Challenge` | `captcha_id→initParameters.captcha_id` (+`version:4`), `risk_type→risk_type` | proxy opt.; UA |
| Turnstile | `TwoCaptchaTurnstileChallenge` | `action→action`, `c_data→cData`, `chl_page_data→chlPageData` | proxy opt.; UA |

#### Anti-Captcha (`anti-captcha`; nine kinds — text via API's `TextCaptchaTask`, absent from the official SDK)

| Kind | Concrete class | Provider extras → wire | Proxy / worker |
|---|---|---|---|
| image | `AntiCaptchaImageChallenge` | `phrase→phrase`, `case→case`, `numeric→numeric`, `math→math`, `min_len→minLength`, `max_len→maxLength`, `comment→comment`, `language_pool→languagePool` | — |
| text | `AntiCaptchaTextChallenge` | `lang→lang` | — |
| reCAPTCHA v2 | `AntiCaptchaRecaptchaV2Challenge` | `data_s→recaptchaDataSValue`, `stoken→websiteSToken`, `is_enterprise→RecaptchaV2EnterpriseTask` (+`enterprisePayload`; no data_s/isInvisible on ent) | proxy opt. (`RecaptchaV2Task`); UA + cookies on proxy-on |
| reCAPTCHA v3 | `AntiCaptchaRecaptchaV3Challenge` | `action→pageAction`, `min_score→minScore` (validated 0.5/0.7/0.9), `is_enterprise→isEnterprise:true` | proxyless only |
| hCaptcha | `AntiCaptchaHCaptchaChallenge` | `rqdata→enterprisePayload` | proxy opt.; UA (also proxyless) + cookies on proxy-on |
| FunCaptcha | `AntiCaptchaFunCaptchaChallenge` | `public_key→websitePublicKey`, `data→data` (blob), `service_url→funcaptchaApiJSSubdomain` | proxy opt.; UA on proxy-on |
| GeeTest v3 | `AntiCaptchaGeeTestV3Challenge` | `gt_key→gt`, `challenge→challenge`, `api_server→geetestApiServerSubdomain`, `geetest_lib→geetestGetLib` | proxy opt.; UA |
| GeeTest v4 | `AntiCaptchaGeeTestV4Challenge` | `captcha_id→gt` (v4 id rides `gt`) + `version:4` + `initParameters`, `risk_type→initParameters.riskType` | proxy opt.; UA |
| Turnstile | `AntiCaptchaTurnstileChallenge` | `action→action`, `c_data→cData`, `chl_page_data→chlPageData` | proxy opt. (`TurnstileTask`; adds `isInvisible` quirk) |

#### CapMonster (`capmonster`; proxyless — no proxy field anywhere, ADR-0012)

| Kind | Concrete class | Provider extras → wire | Worker |
|---|---|---|---|
| image | `CapMonsterImageChallenge` | `module_name→CapMonsterModule` (17-value enum), `threshold→recognizingThreshold` (0-100), `case→Case`, `numeric→numeric`, `math→math` | — |
| reCAPTCHA v2 | `CapMonsterRecaptchaV2Challenge` | `data_s→recaptchaDataSValue`, `is_enterprise→RecaptchaV2EnterpriseTask` (+`enterprisePayload` wrapped `{'s': ...}`, `api_domain→apiDomain`, `action→pageAction`) | UA + cookies |
| reCAPTCHA v3 | `CapMonsterRecaptchaV3Challenge` | `action→pageAction`, `min_score→minScore` (0.1-0.9), `is_enterprise→RecaptchaV3EnterpriseTask` | — |
| hCaptcha | `CapMonsterHCaptchaChallenge` | `rqdata→data`, `fallback_to_actual_ua→fallbackToActualUA` | UA + cookies |
| FunCaptcha | `CapMonsterFunCaptchaChallenge` | `public_key→websitePublicKey`, `data→data` (blob), `service_url→funcaptchaApiJSSubdomain` | UA + cookies |
| GeeTest v3 | `CapMonsterGeeTestV3Challenge` | `gt_key→gt`, `challenge→challenge`, `api_server→geetestApiServerSubdomain`, `geetest_lib→geetestGetLib` | UA |
| GeeTest v4 | `CapMonsterGeeTestV4Challenge` | `captcha_id→initParameters.captcha_id` (+`version:4`), `risk_type→initParameters.riskType` | — |
| Turnstile | `CapMonsterTurnstileChallenge` | `action→pageAction`, `c_data→data`, `chl_page_data→pageData`, `cloudflare_task_type→cloudflareTaskType` (`token` only in v1 — `cf_clearance`/`wait_room` require a proxy, impossible under ADR-0012's proxyless rule), `html_page_base64→htmlPageBase64`, `api_js_url→apiJsUrl` | UA (required for any `cloudflare_task_type`) |

#### Capsolver (`capsolver`; dict-driven SDK — pass-through extras, minimal validation)

| Kind | Concrete class | Provider extras → wire | Proxy / worker |
|---|---|---|---|
| image | `CapsolverImageChallenge` | — (unchecked pass-through) | proxy opt. |
| reCAPTCHA v2 | `CapsolverRecaptchaV2Challenge` | — | proxy opt. (`ReCaptchaV2Task`); UA + cookies pass-through |
| reCAPTCHA v3 | `CapsolverRecaptchaV3Challenge` | `action→pageAction`, `min_score→minScore` | proxyless only |
| hCaptcha | `CapsolverHCaptchaChallenge` | `rqdata→rqdata` | proxy opt.; UA pass-through |
| FunCaptcha | `CapsolverFunCaptchaChallenge` | `public_key→websitePublicKey` | proxy opt. |
| GeeTest v3 | `CapsolverGeeTestV3Challenge` | `gt_key→gt`, `challenge→challenge` | proxy opt. |
| Turnstile | `CapsolverTurnstileChallenge` | `action→metadata.action`, `c_data→metadata.cdata` | proxy opt. (`AntiCloudflareTask`) |

- **Coverage boundary** (ADR-0076): text = 2Captcha + Anti-Captcha only;
  CapMonster/Capsolver have no text task. GeeTest v4 = 2Captcha +
  Anti-Captcha + CapMonster; **Capsolver excluded** (its official SDK
  ships GeeTest v3 only — thin coverage is fine, ADR-0070). reCAPTCHA
  v3 is proxyless-only on Anti-Captcha/CapMonster/Capsolver; 2Captcha
  also offers a proxy variant.

## 3. Solution taxonomy

```
BaseSolution (public abstract root; open for custom kinds; ADR-0056)
+-- ImageSolution          text: str                  (abstract)
+-- TextSolution           text: str                  (abstract)
+-- RecaptchaV2Solution    token: str                 (abstract)
+-- RecaptchaV3Solution    token: str; score; action  (abstract)
+-- HCaptchaSolution       token: str                 (abstract)
+-- FunCaptchaSolution     token: str                 (abstract; ADR-0070)
+-- GeeTestV3Solution      challenge; validate; seccode        (abstract; ADR-0070)
+-- GeeTestV4Solution      captcha_id; lot_number; pass_token; gen_time; captcha_output
                                                           (abstract; ADR-0070)
+-- TurnstileSolution      token: str                 (abstract; ADR-0074)
```

- Bases contain only fields all four providers return for that kind
  (ADR-0035, ADR-0034).
- Provider subclasses add provider-specific extras (e.g. Anti-Captcha's
  `user_agent`, `resp_key` for reCAPTCHA v2); optional provider fields the
  service did not return are `None`, never present in the base.
- Bases **reject direct instantiation** (`TypeError` from `__post_init__` when
  `type(self) is Base`); adapters always construct provider subclasses.
- The universal path types results as `TaskResult[<Kind>Solution]`; facades and
  the challenge->solution link allow statically precise subclasses.

## 4. Models and public types

All models are frozen dataclasses (slots where beneficial; slotscheck in CI)
living in `unicaptcha.types` and re-exported from the root (ADR-0036).

### TaskResult[T]

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
TaskRef`, `submitted_at: datetime` (UTC), `instant_answer: ParsedTask | None`
(ADR-0075; set iff the provider answered the submit itself — instant
tasks). Not user-constructible — provenance is its value. Bridges to
persistence via `.task_ref`.

### TaskStatusResult

Returned by single-shot status queries (ADR-0032, ADR-0050; surface per
ADR-0056 — non-generic, no submission metadata):

| Field | Type |
|---|---|
| `task_id` | `int` |
| `provider` | `str` |
| `status` | `TaskStatus` — enum: `PENDING \| READY \| NO_SOLUTION \| UNKNOWN` |
| `solution` | `BaseSolution \| None` | populated only when READY; narrow via isinstance |
| `cost` | `Decimal \| None` |
| `raw` | `bytes` | untouched response body |

`TaskResult[T]` is the solve()-only return; TaskStatusResult never embeds it.

Provider-side outcomes are always returned values; exceptions on this method
are reserved for caller-side faults (wrong provider -> TypeError, client
closed -> ClientClosedError, transport -> NetworkError).

### TaskEvent

`TaskEvent` describes **what just happened** in the task's life. The
discriminating field is `kind: TaskEventKind` — a named enum, not an
inline union:

```python
class TaskEventKind(Enum):
    PRE_FLIGHT_FAILED   # caller-side fault before any submit attempt (ADR-0045, ADR-0057)
    SUBMIT_REQUESTED    # each createTask attempt sent (#1, #2, #3...)
    SUBMIT_ACCEPTED     # provider accepted; task_id received
    SUBMIT_FAILED       # all submit attempts exhausted; task_id None
    RESULT_REQUESTED    # each getTaskResult check
    RESULT_RECEIVED     # terminal: result obtained
    RESULT_FAILED       # terminal: result polling failed
```

| Field | Type |
|---|---|
| `kind` | `TaskEventKind` | what just happened |
| `provider` | `str` |
| `task_id` | `int \| None` | None on PRE_FLIGHT_FAILED / SUBMIT_REQUESTED / SUBMIT_FAILED; populated from SUBMIT_ACCEPTED onward |
| `elapsed` | `timedelta` | since solve()/wait() start |
| `attempt` | `int` | iteration count within a repeating kind (SUBMIT_REQUESTED #, RESULT_REQUESTED #) |
| `detail` | `str \| None` | e.g. "connection reset", "503"; never credentials; names both parties on TypeError |
| `error_kind` | `ErrorKind \| None` | set only on the terminal failure kinds; `None` on in-progress and success kinds; `None` on PRE_FLIGHT_FAILED caused by wrong-provider `TypeError` (a bare builtin, no ErrorKind) |

Field defaults (settled at implementation): `kind`/`provider`/`elapsed`/
`attempt` are required; `task_id`, `detail`, and `error_kind` default to
`None`.

`error_kind` possible values by kind:

- `PRE_FLIGHT_FAILED`: `INVALID_CHALLENGE`, `UNSUPPORTED_CHALLENGE`,
  `INVALID_CONFIG`, `CLIENT_CLOSED` (at validation), or `None`
  (wrong-provider `TypeError`).
- `SUBMIT_FAILED`: `NETWORK`, `RATE_LIMIT`, `SERVICE_BUSY`,
  `AUTHENTICATION`, `INSUFFICIENT_BALANCE`, `PROVIDER`, `CLIENT_CLOSED`
  (sync close-interrupt).
- `RESULT_FAILED`: `NO_SOLUTION`, `EMPTY_SOLUTION`, `TASK_TIMEOUT`,
  `PROVIDER`, `CLIENT_CLOSED` (sync close-interrupt).

Invariant: every solve invocation ends in exactly one terminal event —
`PRE_FLIGHT_FAILED`, `SUBMIT_FAILED`, `RESULT_FAILED`, or `RESULT_RECEIVED`.
Cancellation is eventless (ADR-0016, ADR-0018).

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
ADR-0028). Construction validates the fail-fast basics — `host` non-empty,
`port` in 1..65535 — raising `InvalidConfigError` (the object is a
configuration value; the same rule applies whether it lands on a challenge
or as the client default). `kind` is enum-enforced; SOCKS4/SOCKS5 support is
provider-side, values sent verbatim. `password` stays plain `str` (masking
contracts are scoped to API keys, ADR-0014). (The sketch above shows
`kind` first; dataclass default-ordering requires the required `host`/
`port` to precede the defaulted `kind` — keyword usage is unaffected.)

Placement: optional `proxy` field on proxy-capable challenges; client-level
default proxy passed as a flat `proxy=` constructor kwarg, applied only to
proxy-capable challenges, challenge field wins. CapMonster is entirely
proxyless; its challenge classes carry no proxy field. Anti-Captcha
accepts proxy IP addresses only — hostname→IP resolution is a network
operation performed by the engine (async-safe, executor-backed) before the
adapter sees the proxy; adapters stay pure (ADR-0041, ADR-0076).

### Worker context (ADR-0069)

`user_agent: str | None` and `cookies: Mapping[str, str] | None` — optional
keyword-only challenge fields the provider's solver uses when loading the
target page (token validity: tokens can be UA-bound). Distinct from the
transport User-Agent (constructor kwarg, ADR-0024); no client-level default,
so the two meanings never share a constructor. Per-provider surface (which
kinds of which providers accept them) lands with deferred item 2.

### SecretStr

Hand-rolled (~30 lines), no pydantic dependency; used for API keys
(ADR-0014).

```python
class SecretStr:
    def __init__(self, value: str): ...
    def get_secret_value(self) -> str: ...
    def __repr__(self) -> str: ...   # fully masked (***)
    def __str__(self) -> str: ...    # fully masked (***)
```

- `repr`/`str` render the value as `***` (full mask — no partial
  characters; keys are short enough that fragments aid guessing).
- Value equality: `__eq__`/`__hash__` compare the wrapped string
  (usable in tests, dedup, registry keys).
- Picklable (consistent with the frozen-data vocabulary).
- Constructors accept `SecretStr | str`; a plain `str` is wrapped at
  the boundary, stored type is always `SecretStr` (ADR-0063).

### repr policy

- Bytes fields render as `<8234 bytes>` stubs, never content.
- Solution tokens/solved text render as `***abcd` (last 4 chars).
- API keys fully masked.
- `str` mirrors `repr`. (ADR-0034)

## 5. Configuration

Three frozen, all-fields-None-able config types (ADR-0043):

```python
NetworkConfig(timeout, max_connections, max_keepalive_connections)
TimeConfig(total_timeout, poll_interval, poll_delay)
RetryConfig(max_attempts, backoff_base, backoff_cap)
```

- Config responsibilities are disjoint though durations appear in both
  `TimeConfig` and `RetryConfig` (ADR-0043 as ratified 2026-08-25):
  `TimeConfig` is the solve-timeline config (budget + poll cadence),
  `RetryConfig` is the retry strategy (count + backoff). `total_timeout`
  is the outer wall-clock budget that contains retry time; the strategy
  shapes the attempts within it.

- `NetworkConfig.timeout` is per-request: the float maps to
  `httpx.Timeout(timeout)`, limiting each stage (connect, read, write,
  pool) independently — distinct from `TimeConfig.total_timeout`, the
  whole-solve budget (ADR-0024).

- `None` means "unspecified", never a value. Explicit bad values
  (`total_timeout=0`, `poll_interval=-5`, `backoff_cap < backoff_base`)
  raise `InvalidConfigError` at config construction; `None` is always
  valid (ADR-0042).
- Resolution chain, field-wise (per-call value -> client value -> per-kind
  default table -> generic fallback). A per-call config **inherits** unset
  fields from the client config; it never discards them.
- Concrete defaults live only in the engine's kind-default table
  (ADR-0030), extended by adapter declarations for custom kinds
  (ADR-0041).
- Identity scalars stay flat constructor kwargs: `name`, `user_agent`,
  `abandoned_registry_limit`, `proxy` (default proxy, ADR-0012).

### Client constructor (ADR-0043 as amended)

`Solver` / `AsyncSolver` take one positional argument and otherwise
keyword-only parameters — `adapters` is the only positional; everything
after `*` must be named (kills the same-typed-swap hazards between the
three configs, `network` vs `network_client`, and the identity scalars;
mirrors the ADR-0066 keyword-only discipline for challenges):

```python
class Solver:
    def __init__(
        self,
        adapters: list[BaseAdapter],               # positional; required, non-empty
        *,
        name: str | None = None,
        user_agent: str | None = None,             # transport User-Agent (ADR-0026)
        proxy: Proxy | None = None,                # default proxy (ADR-0012)
        abandoned_registry_limit: int | None = None,  # ADR-0038
        time: TimeConfig | None = None,
        retry: RetryConfig | None = None,
        network: NetworkConfig | None = None,
        network_client: httpx.Client | None = None,  # mutually exclusive with network= (ADR-0049)
        on_event: Callable[[TaskEvent], None] | None = None,  # sync tier (ADR-0018/0044)
    ): ...

class AsyncSolver:
    def __init__(
        self,
        adapters: list[BaseAdapter],
        *,
        name: str | None = None,
        user_agent: str | None = None,
        proxy: Proxy | None = None,
        abandoned_registry_limit: int | None = None,
        time: TimeConfig | None = None,
        retry: RetryConfig | None = None,
        network: NetworkConfig | None = None,
        network_client: httpx.AsyncClient | None = None,
        on_event: Callable[[TaskEvent], Awaitable[None] | None] | None = None,  # async tier; awaited inline
    ): ...
```

- `on_event` typing and attachment: `on_event` accepted at construction
  and per call; per-call replaces client-level all-or-nothing (ADR-0044).
  The sync tier types the handler `Callable[[TaskEvent], None]`;
  coroutine-function handlers are rejected at attachment with
  `InvalidConfigError`, an awaitable returned at runtime logs a WARNING
  and is discarded. The async tier types it
  `Callable[[TaskEvent], Awaitable[None] | None]`; awaitable results are
  awaited inline. Handler errors propagate raw (ADR-0018).
- Facade constructors (`TwoCaptchaClient` / `AsyncTwoCaptchaClient`)
  follow the same rule: `api_key` positional, then `*`, then keyword-only
  (`base_url`, `referral`, and every client kwarg above except
  `adapters` — ADR-0061/0063/0072).
- Facade convenience methods accept `time=`, `retry=`, `on_event=` with
  identical semantics (ADR-0051).

## 6. Error hierarchy

```
UnicaptchaError                    kind: ErrorKind; raw_response: bytes
+-- NetworkError
+-- AuthenticationError
+-- InsufficientBalanceError
+-- UnsupportedChallengeError        provider lacks the operation/kind (both sides, ADR-0057)
+-- InvalidChallengeError          client-side challenge validation
+-- TaskTimeoutError
+-- RateLimitError
+-- ServiceBusyError               provider capacity: no workers free (ADR-0059 amendment)
+-- NoSolutionError
+-- InvalidConfigError
+-- ClientClosedError
+-- ProviderError                  unclassified provider errors
    +-- EmptySolutionError          solved-but-empty payload (ADR-0040 amendment)
```

- `ErrorKind` (13 values): NETWORK, AUTHENTICATION, INSUFFICIENT_BALANCE, UNSUPPORTED_CHALLENGE,
  INVALID_CHALLENGE, TASK_TIMEOUT, RATE_LIMIT, SERVICE_BUSY, NO_SOLUTION,
  EMPTY_SOLUTION, CLIENT_CLOSED, INVALID_CONFIG, PROVIDER (ADR-0009; ADR-0059
  and ADR-0040 amendments).
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
solve(challenge, provider=None, time=None, retry=None, on_event=None) -> TaskResult[T]
    validate client open
    dispatch challenge -> adapter (universal) or direct (facade):
        concrete class -> its adapter (provider= must match if given, else TypeError)
        kind base + provider="name" -> that adapter (TypeError if unknown,
            UnsupportedChallengeError if kind unsupported)
        kind base + provider=None -> uniform random choice among supporting
            adapters (ADR-0064); upcast to concrete class before build_payload
    submit phase:
        build payload (adapter, pure)
        POST createTask
          - pre-send failure (DNS, refused, TLS, connect-timeout): retry
          - received 500/503: retry
           - rate limit (429 / provider payload): retry, RateLimitError on exhaustion (ADR-0059)
           - busy/no-slots payloads (ERROR_NO_SLOT_AVAILABLE etc.): retry,
             ServiceBusyError on exhaustion (ADR-0059 amendment)
          - read timeout, reset-after-send, 502/504: fail fast NetworkError
          - backoff: full jitter, base 1s, cap 30s, max 3 attempts
     poll phase:
         initial poll_delay before first poll (per-kind; skipped for stale
           tickets in wait() and never applied in wait_ref/get_task_status;
           counted within total_timeout — ADR-0030 amendment)
         POST getTaskResult every poll_interval
           - transient failures tolerated, bounded by total_timeout
           - NO_SOLUTION response -> NoSolutionError (no auto-resubmit)
           - UNKNOWN (task not found) -> ProviderError, fail fast (ADR-0058)
           - solved-but-empty payload -> EmptySolutionError (ADR-0040 amendment)
    terminal:
        READY -> TaskResult[T] (emit RESULT_RECEIVED)
        budget exhausted -> TaskTimeoutError (emit RESULT_FAILED)
        any raised library error emits the matching *_FAILED first, then raises
```

- `total_timeout` covers submit attempts + backoff + polling, starting at the
  `solve()` call (ADR-0010). Enforced internally via `asyncio.timeout()` on
  the async side, converted to `TaskTimeoutError` at our scope boundary
  only; external cancellation passes through untouched.
- Aux operations (`get_balance`, `get_task_status`, `report_bad_result`,
  `report_good_result`, `get_abandoned_tasks`) use the **same** retry
  policy as submission (ADR-0011).
- Polling only; no webhooks (ADR-0015).

### Two-phase operations (ADR-0067)

`solve() = submit() + wait()`, exposed as separate calls on both tiers:

```python
ticket = solver.submit(challenge, provider=None, retry=None, on_event=None)  # -> TaskTicket[T]
result = solver.wait(ticket, timeout=None)                     # -> TaskResult[T], raises on failure
status = solver.wait_ref(TaskRef(...), timeout=120)            # -> TaskStatusResult, answers (PENDING on budget out)
```

- `submit` routes exactly like `solve()` (ADR-0064); bounded by the
  retry policy only — takes `retry=` (RetryConfig) and `on_event=`
  (it emits SUBMIT_REQUESTED/SUBMIT_ACCEPTED/SUBMIT_FAILED), but **no
  `time=`**: submission is not bounded by a total budget, only by
  retries (ADR-0067).
- `wait`: operation semantics — `TaskResult[T]` typed, raises
  (`NoSolutionError`, UNKNOWN -> `ProviderError` per ADR-0058,
  `TaskTimeoutError`); clock starts at the call, default = per-kind
  `total_timeout` (ADR-0030) via the merge chain. Fast path (ADR-0075):
  a ticket with `instant_answer` set returns immediately — no poll, no delay;
  `wait_ref`/`get_task_status` never see the field and poll the provider
  (first poll answers READY).
- `wait_ref`: query semantics — polls until terminal or budget out
  (returns PENDING `TaskStatusResult` on exhaustion).
- `get_task_status` unchanged: single-shot (ADR-0050).
- Events: `SUBMIT_ACCEPTED` at submit; `RESULT_RECEIVED`/`RESULT_FAILED`
  at wait's terminal state; never-waited tickets eventless (ADR-0018 as amended).
  Deferral is not abandonment (ADR-0038 as amended): the registry
  records only cancelled/orphaned waits. Billing caveat: solved but
  uncollected tasks are billed by the provider.


### Auxiliary operations

| Operation | Universal client | Facade |
|---|---|---|
| `get_balance(provider)` | provider discriminator: instance / class / provider string; returns `Decimal` USD | implicit provider |
| `get_task_status(task)` | `TaskRef` | `int \| TaskRef` |
| `report_bad_result(task)` | `TaskRef` | `TaskRef \| int` (returns bool, symmetric with report_good_result) |
| `report_good_result(task)` | `TaskRef` | `TaskRef \| int` (ADR-0068; returns bool, feeds worker quality routing where supported) |
| `get_abandoned_tasks()` | snapshot `tuple[TaskRef, ...]` | same |

Report-bad coverage differs per provider and captcha kind; adapters enforce
the support matrix pre-flight and raise `UnsupportedChallengeError` where the
provider lacks coverage (ADR-0057). Balance is pinned to USD `Decimal`
(ADR-0040).

### Cancellation (ADR-0016)

- `asyncio.CancelledError` propagates untouched; never swallowed, never
  substituted.
- The abandoned `task_id` lands in the abandoned-task registry via
  synchronous bookkeeping (no awaits during cancellation unwinding).
- Billing caveat documented: abandoned tasks may still be billed; reclaim
  via `get_task_status` later.
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
- The abandoned-task registry **survives** close; `get_abandoned_tasks()` remains
  readable afterward (ADR-0038).

### Abandoned-task registry (ADR-0038)

- Typed entries (TaskRef + abandoned-at metadata); thread-safe append-only
  storage; `get_abandoned_tasks()` returns a snapshot tuple, never a live list.
- Bounded: default cap 1000, one WARNING log per eviction, cap configurable
  client-side (`abandoned_registry_limit`), `None` = unbounded.
- Per-client, best-effort, **advisory** (ADR-0060): entries removed when a
  same-client `get_task_status` reaches a terminal state; cleared never
  (survives close); cross-client reclaim leaves stale entries (harmless,
  bounded).
- No automatic reclaim loop; the caller drives reclamation:
  snapshot `get_abandoned_tasks()` -> new client with the same adapters ->
  `get_task_status(ref)` per entry -> terminal states are answers
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
                       # TaskResult, TaskStatusResult, TaskEvent, TaskRef, SecretStr,
                       # configs, Proxy/ProxyKind, challenge/solution kind bases
    _version.py        # single version source (pyproject reads it)
    client.py          # Solver / AsyncSolver
    errors.py          # hierarchy + ErrorKind
    events.py          # TaskEvent
    types.py           # public model vocabulary (TaskResult, TaskStatusResult, TaskRef,
                       # Proxy, SecretStr, configs, kind bases re-exported)
    challenge/         # abstract challenge kind bases (ADR-0048)
        base.py        # BaseChallenge
        image.py       # ImageChallenge
        text.py        # TextChallenge
        recaptcha_v2.py  # RecaptchaV2Challenge
        recaptcha_v3.py  # RecaptchaV3Challenge
        hcaptcha.py    # HCaptchaChallenge
        funcaptcha.py  # FunCaptchaChallenge
        geetest.py     # GeeTestV3Challenge, GeeTestV4Challenge
        turnstile.py   # TurnstileChallenge
    solution/          # abstract solution kind bases (ADR-0035)
        base.py        # BaseSolution
        image.py       # ImageSolution
        text.py        # TextSolution
        recaptcha_v2.py  # RecaptchaV2Solution
        recaptcha_v3.py  # RecaptchaV3Solution
        hcaptcha.py    # HCaptchaSolution
        funcaptcha.py  # FunCaptchaSolution
        geetest.py     # GeeTestV3Solution, GeeTestV4Solution
        turnstile.py   # TurnstileSolution
    provider/          # one package per provider; singular one-per-concern files
        twocaptcha/    # challenge.py, solution.py, adapter.py, client.py
        anticaptcha/
        capmonster/
        capsolver/     # ADR-0071
    _internal/         # engine, http layer implementation, clock, scrubbing,
                       # config resolution (_internal/config.py)
```

- Import model: **eager**. `import unicaptcha` pre-loads provider packages;
  root exposes core vocabulary; provider classes require explicit subpackage
  imports (`from unicaptcha.provider.twocaptcha import ...`).
- Naming rule (ADR-0036 amendment): root package **files** are plural
  (`types.py`, `errors.py`, `events.py`); root package **directories** are
  singular (`challenge/`, `solution/`, `provider/`, `_internal/`); everything
  inside a provider package is singular, one file per concern
  (`challenge.py`, `solution.py`, `adapter.py`, `client.py`).
- Public surface: root + provider packages + the adapter SDK contract
  (`BaseChallenge`, `BaseAdapter` ABC, registration). Everything under
  `_internal/` plus module privates are implementation details. The HTTP
  layer is exposed as a public **Protocol** (what may be injected), while its
  implementation stays internal (ADR-0041).
- Naming: universal `Solver` / `AsyncSolver`; facades
  `<Provider>Client` / `Async<Provider>Client`; challenges
  `<Provider><Kind>Challenge`; solutions `<Provider><Kind>Solution`
  (ADR-0036).
- Facade methods: `solve_image`, `solve_text`, `solve_recaptcha_v2`,
  `solve_recaptcha_v3`, `solve_hcaptcha`, `solve_funcaptcha`,
  `solve_geetest_v3`, `solve_geetest_v4`, `solve_turnstile` — one per kind,
  exposed per-provider based on which kinds that facade supports; aux ops
  named identically on both tiers (`get_balance`, `get_task_status`,
  `report_bad_result`, `report_good_result`, `get_abandoned_tasks`).

### Adapter SDK (ADR-0041)

```python
class MyServiceAdapter(BaseAdapter):
    provider: ClassVar[str] = "myservice"
    challenges: ClassVar[frozenset[type[BaseChallenge]]]
    default_task_config: ClassVar[...]        # per-kind timing defaults; optional
    endpoints: ClassVar[Endpoints]             # JSON-family default; all-or-nothing
                                               # override (ADR-0073): submit,
                                               # get_task_status, get_balance,
                                               # report_good_result, report_bad_result

    def __init__(self, api_key: SecretStr | str, base_url: str | None = None,
                 referral: bool | str = True): ...   # referral per ADR-0072
    def build_payload(self, challenge) -> dict[str, Any]: ...
    def parse_submit_response(self, raw: bytes) -> SubmitAccepted: ...
                                           # SubmitAccepted{task_id: int, instant_answer: ParsedTask | None}
                                           # (ADR-0075); instant_answer set iff createTask answered inline
    def parse_task_status(self, raw: bytes) -> ParsedTask: ...   # pending|ready|unsolvable|unknown (ADR-0058):
                                           # ParsedTask{state, solution, cost, raw, detail} — public
                                           # vocabulary per ADR-0075
    def parse_balance(self, raw: bytes) -> Decimal: ...
    def report_bad_supported(self, challenge_type) -> bool: ...
    def build_report_bad(self, task: TaskRef) -> dict[str, Any]: ...
    def parse_report_bad(self, raw: bytes) -> bool: ...
    def report_good_supported(self, challenge_type) -> bool: ...   # ADR-0068
    def build_report_good(self, task: TaskRef) -> dict[str, Any]: ...
    def parse_report_good(self, raw: bytes) -> bool: ...
    def map_provider_error(self, raw: bytes) -> tuple[ErrorKind, str]: ...
```

- Registration: `Solver(adapters=[MyServiceAdapter(...)])`.
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
