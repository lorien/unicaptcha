from dataclasses import FrozenInstanceError

import pytest

from unicaptcha import InvalidConfigError, Proxy, ProxyKind


class TestProxyKind:
    def test_values(self) -> None:
        assert [k.value for k in ProxyKind] == ["HTTP", "HTTPS", "SOCKS4", "SOCKS5"]


class TestProxy:
    def test_constructible(self) -> None:
        p = Proxy(host="127.0.0.1", port=8080)
        assert p.host == "127.0.0.1"
        assert p.port == 8080
        assert p.kind is ProxyKind.HTTP
        assert p.username is None
        assert p.password is None

    def test_full_fields(self) -> None:
        p = Proxy(
            host="proxy.example.com",
            port=3128,
            kind=ProxyKind.SOCKS5,
            username="u",
            password="p",
        )
        assert p.kind is ProxyKind.SOCKS5
        assert p.password == "p"

    def test_empty_host_raises(self) -> None:
        with pytest.raises(InvalidConfigError):
            Proxy(host="", port=8080)

    def test_port_bounds(self) -> None:
        with pytest.raises(InvalidConfigError):
            Proxy(host="h", port=0)
        with pytest.raises(InvalidConfigError):
            Proxy(host="h", port=65536)

    def test_frozen(self) -> None:
        p = Proxy(host="h", port=1)
        with pytest.raises(FrozenInstanceError):
            p.host = "other"  # type: ignore[misc]
