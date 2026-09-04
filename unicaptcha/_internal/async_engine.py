"""Internal asynchronous TaskEngine (ADR-0010/0011/0016/0018/0030/0050/
0058/0067/0075). Async-native: budgets are clock deadlines checked between
awaits (mirroring the sync engine), so an injected clock + sleep seam makes
timing tests fully deterministic; external cancellation passes through
untouched (ADR-0016)."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from datetime import timedelta
from decimal import Decimal
from typing import Any, Generic, TypeVar, cast

from unicaptcha._internal.backoff import backoff_sleep
from unicaptcha._internal.clock import Clock, RealClock
from unicaptcha._internal.defaults import (
    GENERIC_TIMING,
    ResolvedRetry,
    ResolvedTime,
    resolve_retry,
    resolve_time,
)
from unicaptcha._internal.errors import error_from_kind
from unicaptcha._internal.handlers import emit_async
from unicaptcha._internal.http import AsyncHttpTransport, join_url
from unicaptcha._internal.registry import AbandonedTaskRegistry
from unicaptcha._internal.retry import classify_submit_status, is_presend
from unicaptcha.adapter import BaseAdapter
from unicaptcha.challenge.base import BaseChallenge
from unicaptcha.errors import (
    ClientClosedError,
    ErrorKind,
    NetworkError,
    NoSolutionError,
    ProviderError,
    RateLimitError,
    ServiceBusyError,
    TaskTimeoutError,
)
from unicaptcha.events import AsyncEventHandler, TaskEvent, TaskEventKind
from unicaptcha.solution.base import BaseSolution
from unicaptcha.types import (
    ParsedTask,
    RetryConfig,
    TaskRef,
    TaskResult,
    TaskStatus,
    TaskStatusResult,
    TaskTicket,
    TimeConfig,
)

_T = TypeVar("_T", bound=BaseSolution)
_R = TypeVar("_R")


class AsyncTaskEngine(Generic[_T]):
    """Async-native engine. Cancellation propagates untouched; registry
    mutations (commit 3) are synchronous so they are safe during
    cancellation unwinding (ADR-0016)."""

    def __init__(
        self,
        transport: AsyncHttpTransport,
        *,
        time: TimeConfig | None = None,
        retry: RetryConfig | None = None,
        on_event: AsyncEventHandler | None = None,
        clock: Clock | None = None,
        sleep: Callable[[float], Awaitable[None]] | None = None,
        abandoned_registry_limit: int | None = 1000,
    ) -> None:
        self._transport = transport
        self._client_time = time
        self._client_retry = retry
        self._handler = on_event
        self._clock = clock or RealClock()
        self._sleep_fn = sleep or asyncio.sleep
        self._closed = False
        self._registry = AbandonedTaskRegistry(limit=abandoned_registry_limit)

    async def aclose(self) -> None:
        """Idempotent. In-flight tasks are cancelled by the client
        (ADR-0033); the registry survives and remains readable."""
        self._closed = True
        await self._transport.aclose()

    def get_abandoned_tasks(self) -> tuple[TaskRef, ...]:
        return self._registry.snapshot()

    async def _sleep(self, seconds: float) -> None:
        await self._sleep_fn(seconds)

    def _check_open(self) -> None:
        if self._closed:
            raise ClientClosedError("client is closed")

    async def _retry_pause(self, failures: int, retry: ResolvedRetry) -> None:
        await self._sleep(
            backoff_sleep(failures, retry.backoff_base, retry.backoff_cap)
        )

    def _event(
        self,
        kind: TaskEventKind,
        provider: str,
        start: float,
        *,
        task_id: int | str | None = None,
        attempt: int = 1,
        detail: str | None = None,
        error_kind: ErrorKind | None = None,
    ) -> TaskEvent:
        return TaskEvent(
            kind=kind,
            provider=provider,
            elapsed=timedelta(seconds=self._clock.monotonic() - start),
            attempt=attempt,
            task_id=task_id,
            detail=detail,
            error_kind=error_kind,
        )

    # -- submit ---------------------------------------------------------

    async def submit(
        self,
        adapter: BaseAdapter,
        challenge: BaseChallenge,
        *,
        retry: RetryConfig | None = None,
        on_event: AsyncEventHandler | None = None,
    ) -> TaskTicket[_T]:
        self._check_open()
        retry_cfg = resolve_retry(self._client_retry, retry)
        handler = on_event if on_event is not None else self._handler
        start = self._clock.monotonic()
        url = join_url(adapter.base_url, adapter.endpoints.submit)
        payload = adapter.build_payload(challenge)
        accepted = await self._post_retried(
            adapter,
            url,
            payload,
            retry_cfg,
            handler,
            start,
            adapter.parse_submit_response,
        )
        await emit_async(
            handler,
            self._event(
                TaskEventKind.SUBMIT_ACCEPTED,
                adapter.provider,
                start,
                task_id=accepted.task_id,
            ),
        )
        timing = resolve_time(challenge, adapter, self._client_time, None)
        ref = TaskRef(provider=adapter.provider, task_id=accepted.task_id)
        self._registry.add(ref, self._clock.wallclock())
        return TaskTicket(
            task_ref=ref,
            submitted_at=self._clock.wallclock(),
            instant_answer=accepted.instant_answer,
            time=timing.to_config(),
        )

    async def _post_retried(
        self,
        adapter: BaseAdapter,
        url: str,
        payload: dict[str, Any],
        retry: ResolvedRetry,
        handler: AsyncEventHandler | None,
        start: float,
        parse: Callable[[bytes], _R],
    ) -> _R:
        """POST with the submit-phase retry policy (ADR-0011), then parse.

        Events are emitted only when a handler is given; aux operations
        pass ``None`` (eventless, ADR-0018).
        """
        attempt = 0
        while True:
            self._check_open()
            await emit_async(
                handler,
                self._event(
                    TaskEventKind.SUBMIT_REQUESTED,
                    adapter.provider,
                    start,
                    attempt=attempt + 1,
                ),
            )
            try:
                response = await self._transport.post(url, payload)
            except NetworkError as exc:
                if attempt < retry.max_attempts - 1 and is_presend(exc):
                    await self._retry_pause(attempt, retry)
                    attempt += 1
                    continue
                await self._submit_failed(
                    handler, adapter, start, attempt + 1, ErrorKind.NETWORK, str(exc)
                )
                raise
            kind = classify_submit_status(response.status)
            if kind == "retry" and attempt < retry.max_attempts - 1:
                await self._retry_pause(attempt, retry)
                attempt += 1
                continue
            if kind == "retry_rate_limit":
                if attempt < retry.max_attempts - 1:
                    await self._retry_pause(attempt, retry)
                    attempt += 1
                    continue
                await self._submit_failed(
                    handler,
                    adapter,
                    start,
                    attempt + 1,
                    ErrorKind.RATE_LIMIT,
                    "rate limited",
                )
                raise RateLimitError("rate limited", raw_response=response.body)
            if kind == "fail_fast":
                detail = f"HTTP {response.status}"
                await self._submit_failed(
                    handler, adapter, start, attempt + 1, ErrorKind.NETWORK, detail
                )
                raise NetworkError(detail, raw_response=response.body)
            if kind != "ok":
                err_kind, message = adapter.map_provider_error(response.body)
                await self._submit_failed(
                    handler, adapter, start, attempt + 1, err_kind, message
                )
                raise error_from_kind(err_kind, message, response.body)
            try:
                return parse(response.body)
            except (RateLimitError, ServiceBusyError) as exc:
                if attempt < retry.max_attempts - 1:
                    await self._retry_pause(attempt, retry)
                    attempt += 1
                    continue
                await self._submit_failed(
                    handler, adapter, start, attempt + 1, exc.kind, str(exc)
                )
                raise

    async def _submit_failed(
        self,
        handler: AsyncEventHandler | None,
        adapter: BaseAdapter,
        start: float,
        attempt: int,
        error_kind: ErrorKind,
        detail: str,
    ) -> None:
        await emit_async(
            handler,
            self._event(
                TaskEventKind.SUBMIT_FAILED,
                adapter.provider,
                start,
                attempt=attempt,
                detail=detail,
                error_kind=error_kind,
            ),
        )

    # -- solve ----------------------------------------------------------

    async def solve(
        self,
        adapter: BaseAdapter,
        challenge: BaseChallenge,
        *,
        time: TimeConfig | None = None,
        retry: RetryConfig | None = None,
        on_event: AsyncEventHandler | None = None,
    ) -> TaskResult[_T]:
        self._check_open()
        timing = resolve_time(challenge, adapter, self._client_time, time)
        handler = on_event if on_event is not None else self._handler
        deadline = self._clock.monotonic() + timing.total_timeout
        ticket = await self.submit(adapter, challenge, retry=retry, on_event=handler)
        remaining = max(0.0, deadline - self._clock.monotonic())
        return await self.wait(adapter, ticket, timeout=remaining, on_event=handler)

    # -- wait -----------------------------------------------------------

    async def wait(
        self,
        adapter: BaseAdapter,
        ticket: TaskTicket[_T],
        *,
        timeout: float | None = None,
        on_event: AsyncEventHandler | None = None,
    ) -> TaskResult[_T]:
        self._check_open()
        handler = on_event if on_event is not None else self._handler
        start = self._clock.monotonic()
        if ticket.instant_answer is not None:
            result = self._build_result(adapter, ticket, ticket.instant_answer, start)
            self._registry.remove(ticket.task_ref)
            await emit_async(
                handler,
                self._event(
                    TaskEventKind.RESULT_RECEIVED,
                    adapter.provider,
                    start,
                    task_id=ticket.task_ref.task_id,
                ),
            )
            return result
        timing = ResolvedTime.from_config(ticket.time)
        total = timeout if timeout is not None else timing.total_timeout
        deadline = self._clock.monotonic() + total
        age = self._clock.wallclock() - ticket.submitted_at
        if age < timedelta(seconds=timing.poll_interval):
            await self._sleep(
                min(timing.poll_delay, max(0.0, deadline - self._clock.monotonic()))
            )
        return await self._poll(adapter, ticket, timing, handler, start, deadline)

    async def _poll(
        self,
        adapter: BaseAdapter,
        ticket: TaskTicket[_T],
        timing: ResolvedTime,
        handler: AsyncEventHandler | None,
        start: float,
        deadline: float,
    ) -> TaskResult[_T]:
        url = join_url(adapter.base_url, adapter.endpoints.get_task_status)
        attempt = 0
        while True:
            self._check_open()
            if self._clock.monotonic() >= deadline:
                await emit_async(
                    handler,
                    self._event(
                        TaskEventKind.RESULT_FAILED,
                        adapter.provider,
                        start,
                        task_id=ticket.task_ref.task_id,
                        error_kind=ErrorKind.TASK_TIMEOUT,
                    ),
                )
                raise TaskTimeoutError(
                    f"task {ticket.task_ref.task_id} not solved within "
                    f"{self._clock.monotonic() - start:.3f}s"
                )
            attempt += 1
            await emit_async(
                handler,
                self._event(
                    TaskEventKind.RESULT_REQUESTED,
                    adapter.provider,
                    start,
                    task_id=ticket.task_ref.task_id,
                    attempt=attempt,
                ),
            )
            payload = adapter.build_task_status(ticket.task_ref.task_id)
            try:
                response = await self._transport.post(url, payload)
            except NetworkError:
                await self._sleep(
                    min(
                        timing.poll_interval,
                        max(0.0, deadline - self._clock.monotonic()),
                    )
                )
                continue
            parsed = adapter.parse_task_status(response.body)
            if parsed.state is TaskStatus.READY:
                result = self._build_result(adapter, ticket, parsed, start)
                self._registry.remove(ticket.task_ref)
                await emit_async(
                    handler,
                    self._event(
                        TaskEventKind.RESULT_RECEIVED,
                        adapter.provider,
                        start,
                        task_id=ticket.task_ref.task_id,
                        attempt=attempt,
                    ),
                )
                return result
            if parsed.state is TaskStatus.NO_SOLUTION:
                await emit_async(
                    handler,
                    self._event(
                        TaskEventKind.RESULT_FAILED,
                        adapter.provider,
                        start,
                        task_id=ticket.task_ref.task_id,
                        attempt=attempt,
                        error_kind=ErrorKind.NO_SOLUTION,
                    ),
                )
                raise NoSolutionError(
                    f"task {ticket.task_ref.task_id} could not be solved",
                    raw_response=parsed.raw,
                )
            if parsed.state is TaskStatus.UNKNOWN:
                await emit_async(
                    handler,
                    self._event(
                        TaskEventKind.RESULT_FAILED,
                        adapter.provider,
                        start,
                        task_id=ticket.task_ref.task_id,
                        attempt=attempt,
                        error_kind=ErrorKind.PROVIDER,
                        detail=parsed.detail,
                    ),
                )
                raise ProviderError(
                    parsed.detail or f"task {ticket.task_ref.task_id} not found",
                    raw_response=parsed.raw,
                )
            await self._sleep(
                min(
                    timing.poll_interval,
                    max(0.0, deadline - self._clock.monotonic()),
                )
            )

    # -- aux operations (ADR-0013, ADR-0050, ADR-0067) -------------------

    async def wait_ref(
        self,
        adapter: BaseAdapter,
        ref: TaskRef,
        *,
        timeout: float | None = None,
    ) -> TaskStatusResult:
        """Poll until a terminal state or budget out; answers, never raises
        on provider outcomes (PENDING result on exhaustion, ADR-0067).
        Never applies a poll delay (ADR-0030)."""
        self._check_open()
        total = timeout if timeout is not None else GENERIC_TIMING.total_timeout
        deadline = self._clock.monotonic() + total
        return await self._poll_ref(adapter, ref, deadline)

    async def _poll_ref(
        self, adapter: BaseAdapter, ref: TaskRef, deadline: float
    ) -> TaskStatusResult:
        interval = GENERIC_TIMING.poll_interval
        url = join_url(adapter.base_url, adapter.endpoints.get_task_status)
        while True:
            self._check_open()
            if self._clock.monotonic() >= deadline:
                return TaskStatusResult(
                    task_id=ref.task_id,
                    provider=ref.provider,
                    status=TaskStatus.PENDING,
                    solution=None,
                    cost=None,
                    raw=b"",
                )
            payload = adapter.build_task_status(ref.task_id)
            try:
                response = await self._transport.post(url, payload)
            except NetworkError:
                await self._sleep(
                    min(interval, max(0.0, deadline - self._clock.monotonic()))
                )
                continue
            parsed = adapter.parse_task_status(response.body)
            if parsed.state is not TaskStatus.PENDING:
                self._registry.remove(ref)
                return self._status_result(ref, parsed)
            await self._sleep(
                min(interval, max(0.0, deadline - self._clock.monotonic()))
            )

    async def get_task_status(
        self, adapter: BaseAdapter, ref: TaskRef
    ) -> TaskStatusResult:
        """Single-shot status query; answers (ADR-0050)."""
        self._check_open()
        retry_cfg = resolve_retry(self._client_retry, None)
        url = join_url(adapter.base_url, adapter.endpoints.get_task_status)
        payload = adapter.build_task_status(ref.task_id)
        parsed = await self._post_retried(
            adapter, url, payload, retry_cfg, None, 0.0, adapter.parse_task_status
        )
        if parsed.state is not TaskStatus.PENDING:
            self._registry.remove(ref)
        return self._status_result(ref, parsed)

    async def get_balance(self, adapter: BaseAdapter) -> Decimal:
        self._check_open()
        retry_cfg = resolve_retry(self._client_retry, None)
        url = join_url(adapter.base_url, adapter.endpoints.get_balance)
        payload = adapter.build_balance()
        return await self._post_retried(
            adapter, url, payload, retry_cfg, None, 0.0, adapter.parse_balance
        )

    async def report_bad_result(self, adapter: BaseAdapter, ref: TaskRef) -> bool:
        self._check_open()
        retry_cfg = resolve_retry(self._client_retry, None)
        url = join_url(adapter.base_url, adapter.endpoints.report_bad_result)
        payload = adapter.build_report_bad(ref)
        return await self._post_retried(
            adapter, url, payload, retry_cfg, None, 0.0, adapter.parse_report_bad
        )

    async def report_good_result(self, adapter: BaseAdapter, ref: TaskRef) -> bool:
        self._check_open()
        retry_cfg = resolve_retry(self._client_retry, None)
        url = join_url(adapter.base_url, adapter.endpoints.report_good_result)
        payload = adapter.build_report_good(ref)
        return await self._post_retried(
            adapter, url, payload, retry_cfg, None, 0.0, adapter.parse_report_good
        )

    @staticmethod
    def _status_result(ref: TaskRef, parsed: ParsedTask) -> TaskStatusResult:
        return TaskStatusResult(
            task_id=ref.task_id,
            provider=ref.provider,
            status=parsed.state,
            solution=parsed.solution,
            cost=parsed.cost,
            raw=parsed.raw,
        )

    def _build_result(
        self,
        adapter: BaseAdapter,
        ticket: TaskTicket[_T],
        parsed: ParsedTask,
        start: float,
    ) -> TaskResult[_T]:
        if parsed.solution is None:
            raise ProviderError(
                "READY response carried no solution", raw_response=parsed.raw
            )
        return TaskResult(
            solution=cast(_T, parsed.solution),
            task_id=ticket.task_ref.task_id,
            cost=parsed.cost,
            raw=parsed.raw,
            provider=ticket.task_ref.provider,
            created_at=ticket.submitted_at,
            elapsed=timedelta(seconds=self._clock.monotonic() - start),
        )


__all__ = ["AsyncTaskEngine"]
