# Configuration

All configuration types are frozen dataclasses with `None` fields meaning
**"unspecified"** — the library falls back to its defaults. Explicit
values are validated at construction (`InvalidConfigError` on invalid
ones). Pass them at client construction, or per call where noted.

## TimeConfig — solve timeline

Controls the wall-clock budget and poll cadence of a solve.

| Field | Meaning |
|---|---|
| `total_timeout` | Outer budget for the whole solve, in seconds. |
| `poll_interval` | Seconds between `getTaskResult` polls. |
| `poll_delay` | Initial delay before the first poll (0 by default). |

```python
from unicaptcha import Solver, TimeConfig

client = Solver(
    adapters=[...],
    time=TimeConfig(total_timeout=120.0, poll_interval=2.0, poll_delay=0.0),
)
```

### Default budgets

When unspecified, per-kind defaults apply (ADR-0030), as
`poll_delay / poll_interval / total_timeout`:

| Kind | `poll_delay` | `poll_interval` | `total_timeout` |
|---|---|---|---|
| Image | 5 s | 2 s | 30 s |
| Text | 5 s | 2 s | 120 s |
| reCAPTCHA v2 / v3 | 15 s | 5 s | 120 s |
| hCaptcha | 15 s | 5 s | 120 s |
| Turnstile | 5 s | 3 s | 120 s |
| FunCaptcha | 10 s | 3 s | 180 s |
| GeeTest v3 / v4 | 10 s | 3 s | 180 s |

A provider may ship its own per-kind defaults; the resolved timeline is
`kind default` → `provider default` → `client time=` → `per-call time=`.

## RetryConfig — retry strategy

Controls submit-phase retries (rate limits, service busy, transient
HTTP failures) with full-jitter exponential backoff.

| Field | Meaning |
|---|---|
| `max_attempts` | Maximum number of attempts (including the first). |
| `backoff_base` | Base backoff, doubled per attempt. |
| `backoff_cap` | Upper bound on a single backoff sleep; must be `>= backoff_base`. |

```python
from unicaptcha import RetryConfig

client = Solver(
    adapters=[...],
    retry=RetryConfig(max_attempts=5, backoff_base=1.0, backoff_cap=30.0),
)
```

## NetworkConfig — HTTP layer

| Field | Meaning |
|---|---|
| `timeout` | Per-request timeout in seconds (default 20 s). |
| `max_connections` | HTTP connection pool limit. |
| `max_keepalive_connections` | Keep-alive connection limit. |

```python
from unicaptcha import NetworkConfig

client = Solver(
    adapters=[...],
    network=NetworkConfig(timeout=30.0, max_connections=10),
)
```

## Proxy — structured proxy

A `Proxy` describes a forward proxy. Its `kind` is a `ProxyKind`
(`HTTP`, `HTTPS`, `SOCKS4`, `SOCKS5`).

| Field | Meaning |
|---|---|
| `host` | Host name or IP address (required). |
| `port` | Port in 1..65535 (required). |
| `kind` | `ProxyKind`, default `HTTP`. |
| `username` / `password` | Optional credentials. |

See [Proxy](proxy.md) for usage.

## Passing configs per call

The universal client and the facades accept `time=` and `retry=` per
solving call; `wait(timeout=...)` takes a budget in seconds. Per-call
values override the construction-time values.

## Reference

- [`TimeConfig`, `RetryConfig`, `NetworkConfig`, `Proxy`, `ProxyKind`](../api/types.md)