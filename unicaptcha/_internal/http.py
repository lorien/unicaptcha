"""Internal HTTP transport (ADR-0024, ADR-0026, ADR-0049).

Transport-pure: executes one POST, returns ``(status, body)``, and raises
``NetworkError`` on transport faults. Retry/backoff and HTTP-status policy
live in the engine (task 9), which classifies retryability via the chained
httpx exception (pre-send vs after-send, ADR-0011).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx

from unicaptcha._version import __version__
from unicaptcha.errors import InvalidConfigError, NetworkError
from unicaptcha.types import NetworkConfig

DEFAULT_USER_AGENT = f"unicaptcha/{__version__} (+https://github.com/lorien/unicaptcha)"
_DEFAULT_REQUEST_TIMEOUT = 20.0


def join_url(base_url: str, path: str) -> str:
    """Join a provider base URL and an operation path (ADR-0073)."""
    return base_url.rstrip("/") + path


@dataclass(frozen=True, slots=True)
class HttpResponse:
    """A raw HTTP response: status code and untouched body bytes."""

    status: int
    body: bytes


class HttpTransport:
    """Synchronous transport over an ``httpx.Client``.

    Library-constructed (from ``network`` config or defaults) clients are
    owned and closed by ``close()``; a caller-injected ``network_client``
    is never closed and never mutated (ADR-0024, ADR-0049).
    """

    __slots__ = ("_client", "_owns_client", "_user_agent")

    def __init__(
        self,
        network: NetworkConfig | None = None,
        network_client: httpx.Client | None = None,
        *,
        user_agent: str | None = None,
    ) -> None:
        if network is not None and network_client is not None:
            raise InvalidConfigError(
                "pass either network= config or network_client=, not both"
            )
        self._user_agent = user_agent or DEFAULT_USER_AGENT
        if network_client is not None:
            self._client = network_client
            self._owns_client = False
            return
        if network is not None and network.timeout is not None:
            timeout = network.timeout
        else:
            timeout = _DEFAULT_REQUEST_TIMEOUT
        max_connections = network.max_connections if network else None
        max_keepalive = network.max_keepalive_connections if network else None
        self._client = httpx.Client(
            timeout=httpx.Timeout(timeout),
            limits=httpx.Limits(
                max_connections=max_connections,
                max_keepalive_connections=max_keepalive,
            ),
        )
        self._owns_client = True

    def post(self, url: str, payload: dict[str, Any]) -> HttpResponse:
        try:
            response = self._client.post(
                url,
                json=payload,
                headers={"User-Agent": self._user_agent},
            )
        except httpx.RequestError as exc:
            raise NetworkError(f"network request to {url} failed: {exc}") from exc
        return HttpResponse(status=response.status_code, body=response.content)

    def close(self) -> None:
        if self._owns_client:
            self._client.close()


class AsyncHttpTransport:
    """Asynchronous transport over an ``httpx.AsyncClient``.

    Ownership rules mirror ``HttpTransport``.
    """

    __slots__ = ("_client", "_owns_client", "_user_agent")

    def __init__(
        self,
        network: NetworkConfig | None = None,
        network_client: httpx.AsyncClient | None = None,
        *,
        user_agent: str | None = None,
    ) -> None:
        if network is not None and network_client is not None:
            raise InvalidConfigError(
                "pass either network= config or network_client=, not both"
            )
        self._user_agent = user_agent or DEFAULT_USER_AGENT
        if network_client is not None:
            self._client = network_client
            self._owns_client = False
            return
        if network is not None and network.timeout is not None:
            timeout = network.timeout
        else:
            timeout = _DEFAULT_REQUEST_TIMEOUT
        max_connections = network.max_connections if network else None
        max_keepalive = network.max_keepalive_connections if network else None
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            limits=httpx.Limits(
                max_connections=max_connections,
                max_keepalive_connections=max_keepalive,
            ),
        )
        self._owns_client = True

    async def post(self, url: str, payload: dict[str, Any]) -> HttpResponse:
        try:
            response = await self._client.post(
                url,
                json=payload,
                headers={"User-Agent": self._user_agent},
            )
        except httpx.RequestError as exc:
            raise NetworkError(f"network request to {url} failed: {exc}") from exc
        return HttpResponse(status=response.status_code, body=response.content)

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()


__all__ = [
    "DEFAULT_USER_AGENT",
    "AsyncHttpTransport",
    "HttpResponse",
    "HttpTransport",
    "join_url",
]
