"""The universal multi-provider client (ADR-0005, ADR-0062, ADR-0064).

``Solver`` / ``AsyncSolver`` register adapters (keyed by their provider
string), dispatch challenges to them, and delegate execution to the internal
engines. Routing/validation lives here; execution lives in the engines.
"""

from __future__ import annotations

import threading
import time as _time
from collections.abc import Iterable
from datetime import timedelta
from decimal import Decimal
from typing import Any

import httpx

from unicaptcha._internal.async_engine import AsyncTaskEngine
from unicaptcha._internal.engine import TaskEngine
from unicaptcha._internal.fill import build_fill
from unicaptcha._internal.handlers import check_sync_handler, emit_async, emit_sync
from unicaptcha._internal.http import AsyncHttpTransport, HttpTransport
from unicaptcha._internal.routing import dispatch
from unicaptcha.adapter import BaseAdapter
from unicaptcha.challenge.base import BaseChallenge
from unicaptcha.detect import AutoSolveResult, detect
from unicaptcha.errors import (
    ClientClosedError,
    ErrorKind,
    NoCaptchaDetectedError,
    UnsupportedChallengeError,
)
from unicaptcha.events import (
    AsyncEventHandler,
    SyncEventHandler,
    TaskEvent,
    TaskEventKind,
)
from unicaptcha.types import (
    NetworkConfig,
    Proxy,
    RetryConfig,
    TaskRef,
    TaskResult,
    TaskStatusResult,
    TaskTicket,
    TimeConfig,
)

__all__ = ["AsyncSolver", "Solver"]


def _pre_flight_event(
    provider: str | None,
    start: float,
    detail: str,
    error_kind: ErrorKind | None,
) -> TaskEvent | None:
    """PRE_FLIGHT_FAILED event, or ``None`` when no provider is resolvable."""
    if provider is None:
        return None
    return TaskEvent(
        kind=TaskEventKind.PRE_FLIGHT_FAILED,
        provider=provider,
        elapsed=timedelta(seconds=_time.monotonic() - start),
        attempt=1,
        task_id=None,
        detail=detail,
        error_kind=error_kind,
    )


class Solver:
    """Universal blocking client over a set of registered adapters."""

    __slots__ = ("_closed", "_engine", "_name", "_on_event", "_proxy", "_registry")

    def __init__(
        self,
        adapters: Iterable[BaseAdapter],
        *,
        name: str | None = None,
        user_agent: str | None = None,
        proxy: Proxy | None = None,
        abandoned_registry_limit: int | None = 1000,
        time: TimeConfig | None = None,
        retry: RetryConfig | None = None,
        network: NetworkConfig | None = None,
        network_client: httpx.Client | None = None,
        on_event: SyncEventHandler | None = None,
    ) -> None:
        registry: dict[str, BaseAdapter] = {}
        for item in adapters:
            if not isinstance(item, BaseAdapter):  # pyright: ignore[reportUnnecessaryIsInstance]
                raise TypeError(f"{item!r} is not a BaseAdapter")
            if item.provider in registry:
                raise ValueError(f"provider {item.provider!r} registered twice")
            registry[item.provider] = item
        if not registry:
            raise ValueError("adapters must not be empty")
        check_sync_handler(on_event, what="Solver(adapters | on_event)")
        self._registry = registry
        self._name = name
        self._proxy = proxy
        self._on_event = on_event
        self._closed = False
        transport = HttpTransport(
            network=network, network_client=network_client, user_agent=user_agent
        )
        self._engine: TaskEngine[Any] = TaskEngine(
            transport,
            shutdown=threading.Event(),
            time=time,
            retry=retry,
            on_event=on_event,
            abandoned_registry_limit=abandoned_registry_limit,
        )

    def _check_open(self) -> None:
        if self._closed:
            raise ClientClosedError("client is closed")

    def close(self) -> None:
        if not self._closed:
            self._closed = True
            self._engine.close()

    def __enter__(self) -> Solver:
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()

    def get_abandoned_tasks(self) -> tuple[TaskRef, ...]:
        return self._engine.get_abandoned_tasks()

    def _handler_for(
        self, on_event: SyncEventHandler | None
    ) -> SyncEventHandler | None:
        if on_event is not None:
            check_sync_handler(on_event, what="Solver(on_event=...)")
            return on_event
        return self._on_event

    def _route(
        self,
        challenge: BaseChallenge,
        provider: str | None,
        start: float,
        handler: SyncEventHandler | None,
    ) -> tuple[BaseAdapter, BaseChallenge]:
        def on_pre_flight(
            provider_hint: str | None,
            error_kind: ErrorKind | None,
            message: str,
        ) -> None:
            event = _pre_flight_event(provider_hint, start, message, error_kind)
            if event is not None:
                emit_sync(handler, event)

        return dispatch(self._registry, challenge, provider, self._proxy, on_pre_flight)

    def _adapter_for_ref(self, ref: TaskRef) -> BaseAdapter:
        adapter = self._registry.get(ref.provider)
        if adapter is None:
            raise TypeError(
                f"TaskRef belongs to provider {ref.provider!r}, "
                "which is not registered on this client"
            )
        return adapter

    def _resolve_provider(self, key: object) -> str:
        if isinstance(key, BaseAdapter) or (
            isinstance(key, type) and issubclass(key, BaseAdapter)
        ):
            resolved = key.provider
        elif isinstance(key, str):
            resolved = key
        else:
            raise TypeError(
                f"{key!r} is not a provider string, adapter instance, or adapter class"
            )
        if resolved not in self._registry:
            raise TypeError(f"provider {resolved!r} is not registered")
        return resolved

    # -- operations ------------------------------------------------------

    def solve(
        self,
        challenge: BaseChallenge,
        provider: str | None = None,
        *,
        time: TimeConfig | None = None,
        retry: RetryConfig | None = None,
        on_event: SyncEventHandler | None = None,
    ) -> TaskResult[Any]:
        self._check_open()
        handler = self._handler_for(on_event)
        start = _time.monotonic()
        adapter, prepared = self._route(challenge, provider, start, handler)
        return self._engine.solve(
            adapter, prepared, time=time, retry=retry, on_event=handler
        )

    def auto_solve(
        self,
        html: str,
        pageurl: str,
        provider: str | None = None,
        *,
        time: TimeConfig | None = None,
        retry: RetryConfig | None = None,
        on_event: SyncEventHandler | None = None,
    ) -> AutoSolveResult:
        """Detect and solve the first captcha in ``html`` (ADR-0077).

        Raises ``NoCaptchaDetectedError`` when the page has no supported
        captcha. Pages with several captchas use ``detect()`` + ``solve()``
        directly. The returned ``fill`` maps DOM selectors to the solved
        values; the caller injects them into the live page.
        """
        self._check_open()
        detected = detect(html, pageurl)
        if not detected:
            raise NoCaptchaDetectedError(
                f"no supported captcha detected in page {pageurl!r}"
            )
        first = detected[0]
        result = self.solve(
            first.challenge,
            provider=provider,
            time=time,
            retry=retry,
            on_event=on_event,
        )
        return AutoSolveResult(
            detected=first,
            result=result,
            fill=build_fill(result.solution),
        )

    def submit(
        self,
        challenge: BaseChallenge,
        provider: str | None = None,
        *,
        retry: RetryConfig | None = None,
        on_event: SyncEventHandler | None = None,
    ) -> TaskTicket[Any]:
        self._check_open()
        handler = self._handler_for(on_event)
        start = _time.monotonic()
        adapter, prepared = self._route(challenge, provider, start, handler)
        return self._engine.submit(adapter, prepared, retry=retry, on_event=handler)

    def wait(
        self, ticket: TaskTicket[Any], timeout: float | None = None
    ) -> TaskResult[Any]:
        self._check_open()
        adapter = self._adapter_for_ref(ticket.task_ref)
        return self._engine.wait(adapter, ticket, timeout=timeout)

    def wait_ref(self, ref: TaskRef, timeout: float | None = None) -> TaskStatusResult:
        self._check_open()
        return self._engine.wait_ref(self._adapter_for_ref(ref), ref, timeout=timeout)

    def get_task_status(self, ref: TaskRef) -> TaskStatusResult:
        self._check_open()
        return self._engine.get_task_status(self._adapter_for_ref(ref), ref)

    def get_balance(self, provider: BaseAdapter | type[BaseAdapter] | str) -> Decimal:
        self._check_open()
        name = self._resolve_provider(provider)
        return self._engine.get_balance(self._registry[name])

    def report_bad_result(self, task: TaskRef) -> bool:
        self._check_open()
        return self._engine.report_bad_result(self._adapter_for_ref(task), task)

    def report_good_result(self, task: TaskRef) -> bool:
        self._check_open()
        return self._engine.report_good_result(self._adapter_for_ref(task), task)


class AsyncSolver:
    """Universal asyncio-native client over a set of registered adapters."""

    __slots__ = ("_closed", "_engine", "_name", "_on_event", "_proxy", "_registry")

    def __init__(
        self,
        adapters: Iterable[BaseAdapter],
        *,
        name: str | None = None,
        user_agent: str | None = None,
        proxy: Proxy | None = None,
        abandoned_registry_limit: int | None = 1000,
        time: TimeConfig | None = None,
        retry: RetryConfig | None = None,
        network: NetworkConfig | None = None,
        network_client: httpx.AsyncClient | None = None,
        on_event: AsyncEventHandler | None = None,
    ) -> None:
        registry: dict[str, BaseAdapter] = {}
        for item in adapters:
            if not isinstance(item, BaseAdapter):  # pyright: ignore[reportUnnecessaryIsInstance]
                raise TypeError(f"{item!r} is not a BaseAdapter")
            if item.provider in registry:
                raise ValueError(f"provider {item.provider!r} registered twice")
            registry[item.provider] = item
        if not registry:
            raise ValueError("adapters must not be empty")
        self._registry = registry
        self._name = name
        self._proxy = proxy
        self._on_event = on_event
        self._closed = False
        transport = AsyncHttpTransport(
            network=network, network_client=network_client, user_agent=user_agent
        )
        self._engine: AsyncTaskEngine[Any] = AsyncTaskEngine(
            transport,
            time=time,
            retry=retry,
            on_event=on_event,
            abandoned_registry_limit=abandoned_registry_limit,
        )

    def _check_open(self) -> None:
        if self._closed:
            raise ClientClosedError("client is closed")

    async def aclose(self) -> None:
        if not self._closed:
            self._closed = True
            await self._engine.aclose()

    async def __aenter__(self) -> AsyncSolver:
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        await self.aclose()

    def get_abandoned_tasks(self) -> tuple[TaskRef, ...]:
        return self._engine.get_abandoned_tasks()

    def _handler_for(
        self, on_event: AsyncEventHandler | None
    ) -> AsyncEventHandler | None:
        return on_event if on_event is not None else self._on_event

    def _adapter_for_ref(self, ref: TaskRef) -> BaseAdapter:
        adapter = self._registry.get(ref.provider)
        if adapter is None:
            raise TypeError(
                f"TaskRef belongs to provider {ref.provider!r}, "
                "which is not registered on this client"
            )
        return adapter

    def _resolve_provider(self, key: object) -> str:
        if isinstance(key, BaseAdapter) or (
            isinstance(key, type) and issubclass(key, BaseAdapter)
        ):
            resolved = key.provider
        elif isinstance(key, str):
            resolved = key
        else:
            raise TypeError(
                f"{key!r} is not a provider string, adapter instance, or adapter class"
            )
        if resolved not in self._registry:
            raise TypeError(f"provider {resolved!r} is not registered")
        return resolved

    async def _route(
        self,
        challenge: BaseChallenge,
        provider: str | None,
        start: float,
        handler: AsyncEventHandler | None,
    ) -> tuple[BaseAdapter, BaseChallenge]:
        pending: list[TaskEvent] = []

        def on_pre_flight(
            provider_hint: str | None,
            error_kind: ErrorKind | None,
            message: str,
        ) -> None:
            event = _pre_flight_event(provider_hint, start, message, error_kind)
            if event is not None:
                pending.append(event)

        try:
            return dispatch(
                self._registry, challenge, provider, self._proxy, on_pre_flight
            )
        except (TypeError, UnsupportedChallengeError):
            for event in pending:
                await emit_async(handler, event)
            raise

    # -- operations ------------------------------------------------------

    async def solve(
        self,
        challenge: BaseChallenge,
        provider: str | None = None,
        *,
        time: TimeConfig | None = None,
        retry: RetryConfig | None = None,
        on_event: AsyncEventHandler | None = None,
    ) -> TaskResult[Any]:
        self._check_open()
        handler = self._handler_for(on_event)
        start = _time.monotonic()
        adapter, prepared = await self._route(challenge, provider, start, handler)
        return await self._engine.solve(
            adapter, prepared, time=time, retry=retry, on_event=handler
        )

    async def auto_solve(
        self,
        html: str,
        pageurl: str,
        provider: str | None = None,
        *,
        time: TimeConfig | None = None,
        retry: RetryConfig | None = None,
        on_event: AsyncEventHandler | None = None,
    ) -> AutoSolveResult:
        """Detect and solve the first captcha in ``html`` (ADR-0077).

        Raises ``NoCaptchaDetectedError`` when the page has no supported
        captcha. Pages with several captchas use ``detect()`` + ``solve()``
        directly. The returned ``fill`` maps DOM selectors to the solved
        values; the caller injects them into the live page.
        """
        self._check_open()
        detected = detect(html, pageurl)
        if not detected:
            raise NoCaptchaDetectedError(
                f"no supported captcha detected in page {pageurl!r}"
            )
        first = detected[0]
        result = await self.solve(
            first.challenge,
            provider=provider,
            time=time,
            retry=retry,
            on_event=on_event,
        )
        return AutoSolveResult(
            detected=first,
            result=result,
            fill=build_fill(result.solution),
        )

    async def submit(
        self,
        challenge: BaseChallenge,
        provider: str | None = None,
        *,
        retry: RetryConfig | None = None,
        on_event: AsyncEventHandler | None = None,
    ) -> TaskTicket[Any]:
        self._check_open()
        handler = self._handler_for(on_event)
        start = _time.monotonic()
        adapter, prepared = await self._route(challenge, provider, start, handler)
        return await self._engine.submit(
            adapter, prepared, retry=retry, on_event=handler
        )

    async def wait(
        self, ticket: TaskTicket[Any], timeout: float | None = None
    ) -> TaskResult[Any]:
        self._check_open()
        adapter = self._adapter_for_ref(ticket.task_ref)
        return await self._engine.wait(adapter, ticket, timeout=timeout)

    async def wait_ref(
        self, ref: TaskRef, timeout: float | None = None
    ) -> TaskStatusResult:
        self._check_open()
        return await self._engine.wait_ref(
            self._adapter_for_ref(ref), ref, timeout=timeout
        )

    async def get_task_status(self, ref: TaskRef) -> TaskStatusResult:
        self._check_open()
        return await self._engine.get_task_status(self._adapter_for_ref(ref), ref)

    async def get_balance(
        self, provider: BaseAdapter | type[BaseAdapter] | str
    ) -> Decimal:
        self._check_open()
        name = self._resolve_provider(provider)
        return await self._engine.get_balance(self._registry[name])

    async def report_bad_result(self, task: TaskRef) -> bool:
        self._check_open()
        return await self._engine.report_bad_result(self._adapter_for_ref(task), task)

    async def report_good_result(self, task: TaskRef) -> bool:
        self._check_open()
        return await self._engine.report_good_result(self._adapter_for_ref(task), task)


__all__ = ["AsyncSolver", "Solver"]
