# Task 8: HTTP layer

Status: new

Implement the internal HTTP layer behind the public Protocol:

- httpx wiring: `NetworkConfig.timeout` maps to `httpx.Timeout(timeout)`,
  per-stage; `max_connections` / `max_keepalive_connections`.
- Per-request User-Agent (constructor `user_agent=`); default from
  ADR-0026.
- Ownership rules: library-constructed HTTP layer closed by `close()`;
  caller-injected `network_client` never closed; `network=...` plus
  injected client rejected (`InvalidConfigError`, mutual exclusion).
- Sole injection seam for network resources; engine builds URLs as
  `adapter.base_url + adapter.endpoints.<operation>`.

References: ADR-0024, ADR-0026, ADR-0041, ADR-0049, ADR-0073.

## Done

- `unicaptcha/_internal/http.py`: `HttpResponse` (status/body frozen
  dataclass), `join_url(base_url, path)` helper (for the engine, ADR-0073),
  `HttpTransport` (sync) and `AsyncHttpTransport` (async), both with
  `__slots__`.
- Transport-pure (owner decision): one `post(url, payload: dict) ->
  HttpResponse`; `httpx.RequestError` -> `NetworkError` chained `from`.
  Retry/backoff and HTTP-status policy stay in the engine (task 9), which
  classifies retryability via the chained httpx exception (pre-send vs
  after-send, ADR-0011).
- Constructor `(network: NetworkConfig | None, network_client: httpx.Client |
  None, *, user_agent: str | None)`: both given -> `InvalidConfigError`
  (ADR-0049). Library-built client from `network`/defaults (owned, closed
  by `close()`/`aclose()`); injected client never closed/mutated.
- `network.timeout` maps to `httpx.Timeout(timeout)` (per-stage), pool
  limits to `httpx.Limits(...)`, default request timeout 20 s (ADR-0024).
- Per-request `User-Agent` (default `unicaptcha/<version>
  (+https://github.com/lorien/unicaptcha)`, ADR-0026 + `__version__`;
  `user_agent=` override), never on client defaults (ADR-0049).
- No custom Protocol class (owner decision): the injection type is
  `httpx.Client`/`httpx.AsyncClient`.
- Tests (162 total passing): construction (defaults/config mapping/injected/
  mutual exclusion/UA), POST JSON + UA header + status/body passthrough,
  transport error -> chained `NetworkError`, ownership close semantics,
  async equivalents, `join_url`.
- Full suite green (ruff, mypy strict, pyright strict, slotscheck, pytest).
  No hard-coded credentials.