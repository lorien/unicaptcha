import httpx
import pytest
import respx

from unicaptcha import InvalidConfigError, NetworkConfig, NetworkError
from unicaptcha._internal.http import (
    DEFAULT_USER_AGENT,
    AsyncHttpTransport,
    HttpResponse,
    HttpTransport,
    join_url,
)

URL = "https://api.example.com/createTask"
PAYLOAD = {"key": "value"}


class TestJoinUrl:
    def test_join(self) -> None:
        assert join_url("https://api.x.com", "/createTask") == (
            "https://api.x.com/createTask"
        )
        assert join_url("https://api.x.com/", "/createTask") == (
            "https://api.x.com/createTask"
        )


class TestConstruction:
    def test_default_builds_owned_client(self) -> None:
        t = HttpTransport()
        assert t._owns_client is True
        assert t._user_agent == DEFAULT_USER_AGENT
        t.close()

    def test_network_config_maps_timeout_and_limits(self) -> None:
        t = HttpTransport(
            NetworkConfig(timeout=5, max_connections=3, max_keepalive_connections=2)
        )
        assert t._client.timeout == httpx.Timeout(5)
        pool = t._client._transport._pool
        assert pool._max_connections == 3
        assert pool._max_keepalive_connections == 2
        t.close()

    def test_empty_network_config_uses_default_timeout(self) -> None:
        t = HttpTransport(NetworkConfig())
        assert t._client.timeout == httpx.Timeout(20)
        t.close()

    def test_injected_client_not_owned(self) -> None:
        client = httpx.Client()
        try:
            t = HttpTransport(network_client=client)
            assert t._owns_client is False
        finally:
            client.close()

    def test_user_agent_override(self) -> None:
        t = HttpTransport(user_agent="my-agent/1.0")
        assert t._user_agent == "my-agent/1.0"
        t.close()

    def test_network_and_injected_client_rejected(self) -> None:
        client = httpx.Client()
        try:
            with pytest.raises(InvalidConfigError):
                HttpTransport(NetworkConfig(), client)
        finally:
            client.close()


class TestPost:
    def test_posts_json_with_user_agent(self) -> None:
        with respx.mock:
            route = respx.post(URL).mock(
                return_value=httpx.Response(200, json={"ok": True})
            )
            t = HttpTransport()
            r = t.post(URL, PAYLOAD)
            assert r == HttpResponse(status=200, body=b'{"ok":true}')
            req = route.calls.last.request
            assert req.headers["user-agent"] == DEFAULT_USER_AGENT
            assert req.content == b'{"key":"value"}'

    def test_override_user_agent_sent(self) -> None:
        with respx.mock:
            route = respx.post(URL).mock(
                return_value=httpx.Response(200, content=b"body")
            )
            t = HttpTransport(user_agent="my-agent/1.0")
            t.post(URL, PAYLOAD)
            assert route.calls.last.request.headers["user-agent"] == "my-agent/1.0"

    def test_non_200_status_passes_through(self) -> None:
        with respx.mock:
            respx.post(URL).mock(return_value=httpx.Response(429, content=b"slow down"))
            t = HttpTransport()
            r = t.post(URL, PAYLOAD)
            assert r.status == 429
            assert r.body == b"slow down"

    def test_transport_error_raises_network_error(self) -> None:
        with respx.mock:
            respx.post(URL).mock(side_effect=httpx.ConnectError("boom"))
            t = HttpTransport()
            with pytest.raises(NetworkError) as excinfo:
                t.post(URL, PAYLOAD)
            assert isinstance(excinfo.value.__cause__, httpx.ConnectError)


class TestOwnership:
    def test_owned_client_closed(self) -> None:
        t = HttpTransport()
        t.close()
        assert t._client.is_closed

    def test_injected_client_not_closed(self) -> None:
        client = httpx.Client()
        try:
            t = HttpTransport(network_client=client)
            t.close()
            assert client.is_closed is False
        finally:
            client.close()


class TestAsync:
    @pytest.mark.asyncio
    async def test_post_awaits_with_user_agent(self) -> None:
        with respx.mock:
            route = respx.post(URL).mock(
                return_value=httpx.Response(201, content=b"ok")
            )
            t = AsyncHttpTransport()
            r = await t.post(URL, PAYLOAD)
            assert r.status == 201
            assert r.body == b"ok"
            assert route.calls.last.request.headers["user-agent"] == DEFAULT_USER_AGENT

    @pytest.mark.asyncio
    async def test_transport_error_raises_network_error(self) -> None:
        with respx.mock:
            respx.post(URL).mock(side_effect=httpx.ConnectError("boom"))
            t = AsyncHttpTransport()
            with pytest.raises(NetworkError) as excinfo:
                await t.post(URL, PAYLOAD)
            assert isinstance(excinfo.value.__cause__, httpx.ConnectError)

    @pytest.mark.asyncio
    async def test_owned_client_closed(self) -> None:
        t = AsyncHttpTransport()
        await t.aclose()
        assert t._client.is_closed

    @pytest.mark.asyncio
    async def test_injected_client_not_closed(self) -> None:
        client = httpx.AsyncClient()
        try:
            t = AsyncHttpTransport(network_client=client)
            await t.aclose()
            assert client.is_closed is False
        finally:
            await client.aclose()

    @pytest.mark.asyncio
    async def test_network_and_injected_client_rejected(self) -> None:
        client = httpx.AsyncClient()
        try:
            with pytest.raises(InvalidConfigError):
                AsyncHttpTransport(NetworkConfig(), client)
        finally:
            await client.aclose()
