"""Internal synchronous TaskEngine (ADR-0010/0011/0018/0030/0050/0058/0067/
0075). The client (task 10) resolves routing and passes the adapter per
call; this engine executes submit -> poll -> result on a given adapter."""

from __future__ import annotations

import threading
from collections.abc import Callable
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
from unicaptcha._internal.handlers import emit_sync
from unicaptcha._internal.http import HttpTransport, join_url
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
from unicaptcha.events import SyncEventHandler, TaskEvent, TaskEventKind
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


class TaskEngine(Generic[_T]):
    """Synchronous engine. Real blocking (ADR-0003); sleeps honor the
    shutdown event so ``close()`` wakes blocked solves (ADR-0033)."""

    def __init__(
        self,
        transport: HttpTransport,
        *,
        shutdown: threading.Event,
        time: TimeConfig | None = None,
        retry: RetryConfig | None = None,
        on_event: SyncEventHandler | None = None,
        clock: Clock | None = None,
        abandoned_registry_limit: int | None = 1000,
    ) -> None:
        self._transport = transport
        self._shutdown = shutdown
        self._client_time = time
        self._client_retry = retry
        self._handler = on_event
        self._clock = clock or RealClock()
        self._registry = AbandonedTaskRegistry(limit=abandoned_registry_limit)

    def close(self) -> None:
        """Idempotent: wake blocked solves at their next checkpoint, close
        the transport if library-owned. The registry survives (ADR-0033)."""
        self._shutdown.set()
        self._transport.close()

    def get_abandoned_tasks(self) -> tuple[TaskRef, ...]:
        return self._registry.snapshot()

    def _sleep(self, seconds: float) -> None:
        self._shutdown.wait(timeout=seconds)

    def _check_open(self) -> None:
        if self._shutdown.is_set():
            raise ClientClosedError("client is closed")

    def _retry_pause(self, failures: int, retry: ResolvedRetry) -> None:
        self._sleep(backoff_sleep(failures, retry.backoff_base, retry.backoff_cap))

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

    def submit(
        self,
        adapter: BaseAdapter,
        challenge: BaseChallenge,
        *,
        retry: RetryConfig | None = None,
        on_event: SyncEventHandler | None = None,
    ) -> TaskTicket[_T]:
        self._check_open()
        retry_cfg = resolve_retry(self._client_retry, retry)
        handler = on_event if on_event is not None else self._handler
        start = self._clock.monotonic()
        url = join_url(adapter.base_url, adapter.endpoints.submit)
        payload = adapter.build_payload(challenge)
        accepted = self._post_retried(
            adapter,
            url,
            payload,
            retry_cfg,
            handler,
            start,
            adapter.parse_submit_response,
        )
        emit_sync(
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

    def _post_retried(
        self,
        adapter: BaseAdapter,
        url: str,
        payload: dict[str, Any],
        retry: ResolvedRetry,
        handler: SyncEventHandler | None,
        start: float,
        parse: Callable[[bytes], _R],
    ) -> _R:
        """POST with the submit-phase retry policy (ADR-0011), then parse.

        Events (SUBMIT_REQUESTED/SUBMIT_FAILED) are emitted only when a
        handler is given; the aux operations pass ``None`` — they share the
        retry policy but are eventless (ADR-0018 kinds are solve-lifecycle
        only).
        """
        attempt = 0
        while True:
            self._check_open()
            emit_sync(
                handler,
                self._event(
                    TaskEventKind.SUBMIT_REQUESTED,
                    adapter.provider,
                    start,
                    attempt=attempt + 1,
                ),
            )
            try:
                response = self._transport.post(url, payload)
            except NetworkError as exc:
                if attempt < retry.max_attempts - 1 and is_presend(exc):
                    self._retry_pause(attempt, retry)
                    attempt += 1
                    continue
                self._submit_failed(
                    handler, adapter, start, attempt + 1, ErrorKind.NETWORK, str(exc)
                )
                raise
            kind = classify_submit_status(response.status)
            if kind == "retry" and attempt < retry.max_attempts - 1:
                self._retry_pause(attempt, retry)
                attempt += 1
                continue
            if kind == "retry_rate_limit":
                if attempt < retry.max_attempts - 1:
                    self._retry_pause(attempt, retry)
                    attempt += 1
                    continue
                self._submit_failed(
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
                self._submit_failed(
                    handler, adapter, start, attempt + 1, ErrorKind.NETWORK, detail
                )
                raise NetworkError(detail, raw_response=response.body)
            if kind != "ok":
                err_kind, message = adapter.map_provider_error(response.body)
                self._submit_failed(
                    handler, adapter, start, attempt + 1, err_kind, message
                )
                raise error_from_kind(err_kind, message, response.body)
            try:
                return parse(response.body)
            except (RateLimitError, ServiceBusyError) as exc:
                if attempt < retry.max_attempts - 1:
                    self._retry_pause(attempt, retry)
                    attempt += 1
                    continue
                self._submit_failed(
                    handler, adapter, start, attempt + 1, exc.kind, str(exc)
                )
                raise

    def _submit_failed(
        self,
        handler: SyncEventHandler | None,
        adapter: BaseAdapter,
        start: float,
        attempt: int,
        error_kind: ErrorKind,
        detail: str,
    ) -> None:
        emit_sync(
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

    def solve(
        self,
        adapter: BaseAdapter,
        challenge: BaseChallenge,
        *,
        time: TimeConfig | None = None,
        retry: RetryConfig | None = None,
        on_event: SyncEventHandler | None = None,
    ) -> TaskResult[_T]:
        self._check_open()
        timing = resolve_time(challenge, adapter, self._client_time, time)
        handler = on_event if on_event is not None else self._handler
        ticket = self.submit(adapter, challenge, retry=retry, on_event=handler)
        return self.wait(
            adapter, ticket, timeout=timing.total_timeout, on_event=handler
        )

    # -- wait -----------------------------------------------------------

    def wait(
        self,
        adapter: BaseAdapter,
        ticket: TaskTicket[_T],
        *,
        timeout: float | None = None,
        on_event: SyncEventHandler | None = None,
    ) -> TaskResult[_T]:
        self._check_open()
        handler = on_event if on_event is not None else self._handler
        start = self._clock.monotonic()
        if ticket.instant_answer is not None:
            result = self._build_result(adapter, ticket, ticket.instant_answer, start)
            self._registry.remove(ticket.task_ref)
            emit_sync(
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
            self._sleep(
                min(timing.poll_delay, max(0.0, deadline - self._clock.monotonic()))
            )
        while True:
            self._check_open()
            if self._clock.monotonic() >= deadline:
                emit_sync(
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
                    f"task {ticket.task_ref.task_id} not solved within {total}s"
                )
            emit_sync(
                handler,
                self._event(
                    TaskEventKind.RESULT_REQUESTED,
                    adapter.provider,
                    start,
                    task_id=ticket.task_ref.task_id,
                ),
            )
            url = join_url(adapter.base_url, adapter.endpoints.get_task_status)
            payload = adapter.build_task_status(ticket.task_ref.task_id)
            try:
                response = self._transport.post(url, payload)
            except NetworkError:
                self._sleep(
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
                emit_sync(
                    handler,
                    self._event(
                        TaskEventKind.RESULT_RECEIVED,
                        adapter.provider,
                        start,
                        task_id=ticket.task_ref.task_id,
                    ),
                )
                return result
            if parsed.state is TaskStatus.NO_SOLUTION:
                emit_sync(
                    handler,
                    self._event(
                        TaskEventKind.RESULT_FAILED,
                        adapter.provider,
                        start,
                        task_id=ticket.task_ref.task_id,
                        error_kind=ErrorKind.NO_SOLUTION,
                    ),
                )
                raise NoSolutionError(
                    f"task {ticket.task_ref.task_id} could not be solved",
                    raw_response=parsed.raw,
                )
            if parsed.state is TaskStatus.UNKNOWN:
                emit_sync(
                    handler,
                    self._event(
                        TaskEventKind.RESULT_FAILED,
                        adapter.provider,
                        start,
                        task_id=ticket.task_ref.task_id,
                        error_kind=ErrorKind.PROVIDER,
                        detail=parsed.detail,
                    ),
                )
                raise ProviderError(
                    parsed.detail or f"task {ticket.task_ref.task_id} not found",
                    raw_response=parsed.raw,
                )
            self._sleep(
                min(timing.poll_interval, max(0.0, deadline - self._clock.monotonic()))
            )

    # -- aux operations (ADR-0013, ADR-0050, ADR-0067) -------------------

    def wait_ref(
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
                response = self._transport.post(url, payload)
            except NetworkError:
                self._sleep(min(interval, max(0.0, deadline - self._clock.monotonic())))
                continue
            parsed = adapter.parse_task_status(response.body)
            if parsed.state is not TaskStatus.PENDING:
                self._registry.remove(ref)
                return self._status_result(ref, parsed)
            self._sleep(min(interval, max(0.0, deadline - self._clock.monotonic())))

    def get_task_status(self, adapter: BaseAdapter, ref: TaskRef) -> TaskStatusResult:
        """Single-shot status query; answers (ADR-0050)."""
        self._check_open()
        retry_cfg = resolve_retry(self._client_retry, None)
        url = join_url(adapter.base_url, adapter.endpoints.get_task_status)
        payload = adapter.build_task_status(ref.task_id)
        parsed = self._post_retried(
            adapter, url, payload, retry_cfg, None, 0.0, adapter.parse_task_status
        )
        if parsed.state is not TaskStatus.PENDING:
            self._registry.remove(ref)
        return self._status_result(ref, parsed)

    def get_balance(self, adapter: BaseAdapter) -> Decimal:
        self._check_open()
        retry_cfg = resolve_retry(self._client_retry, None)
        url = join_url(adapter.base_url, adapter.endpoints.get_balance)
        payload = adapter.build_balance()
        return self._post_retried(
            adapter, url, payload, retry_cfg, None, 0.0, adapter.parse_balance
        )

    def report_bad_result(self, adapter: BaseAdapter, ref: TaskRef) -> bool:
        self._check_open()
        retry_cfg = resolve_retry(self._client_retry, None)
        url = join_url(adapter.base_url, adapter.endpoints.report_bad_result)
        payload = adapter.build_report_bad(ref)
        return self._post_retried(
            adapter, url, payload, retry_cfg, None, 0.0, adapter.parse_report_bad
        )

    def report_good_result(self, adapter: BaseAdapter, ref: TaskRef) -> bool:
        self._check_open()
        retry_cfg = resolve_retry(self._client_retry, None)
        url = join_url(adapter.base_url, adapter.endpoints.report_good_result)
        payload = adapter.build_report_good(ref)
        return self._post_retried(
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


__all__ = ["TaskEngine"]
