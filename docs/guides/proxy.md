# Proxy

The library accepts structured forward proxies. Proxy handling is
**provider-scoped**: a proxy is only sent when the concrete challenge
class carries a `proxy` field (most providers support it for token
kinds; image/text are typically proxyless). If a provider does not
support proxies for a kind, the proxy is ignored and a warning is
logged.

## Per-challenge proxy

Use the concrete provider challenge class with its `proxy=` field:

```python
from unicaptcha import Proxy, ProxyKind
from unicaptcha.provider.twocaptcha import TwoCaptchaRecaptchaV2Challenge

proxy = Proxy(
    host="127.0.0.1",
    port=8080,
    kind=ProxyKind.HTTP,
    username="user",
    password="pass",
)

challenge = TwoCaptchaRecaptchaV2Challenge(
    sitekey="SITEKEY",
    pageurl="https://example.com",
    proxy=proxy,
)
```

## Client default proxy

Both `Solver` and the facades accept a `proxy=` at construction. The
default is applied only to challenges that carry a `proxy` field and do
not set their own:

```python
from unicaptcha import Proxy, Solver
from unicaptcha.provider.twocaptcha import TwoCaptchaAdapter

client = Solver(
    adapters=[TwoCaptchaAdapter("YOUR_API_KEY")],
    proxy=Proxy(host="127.0.0.1", port=8080),
)
```

A challenge's own proxy always wins over the client default.

## ProxyKind

| Value | Scheme |
|---|---|
| `ProxyKind.HTTP` | HTTP proxy |
| `ProxyKind.HTTPS` | HTTPS proxy |
| `ProxyKind.SOCKS4` | SOCKS4 proxy |
| `ProxyKind.SOCKS5` | SOCKS5 proxy |

## Validation

`Proxy` validates at construction: `host` must be non-empty and `port`
in 1..65535, otherwise `InvalidConfigError` is raised.

## Reference

- [`Proxy` / `ProxyKind`](../api/types.md)